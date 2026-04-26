import cv2
import numpy as np
import time
import os
import serial
import sys
import json

# ==========================================
# KONFIGURACJA BOTA
# ==========================================
TEST_MODE = False
TEST_IMAGE_PATH = 'testing_img/shiny_charmander.webp'
PORT_COM = 'COM11'
COUNTER_FILE = 'encounters.json'

ROI_X = 825
ROI_Y = 220
ROI_W = 80
ROI_H = 80

# Czas spamowania przycisku A (Dostosuj do gry)
TIME_TO_MASH_A = 40.0


# ==========================================
# FUNKCJE POMOCNICZE
# ==========================================
def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            try:
                data = json.load(f)
                return data.get('encounters', 0)
            except:
                return 0
    return 0


def save_counter(count):
    with open(COUNTER_FILE, 'w') as f:
        json.dump({'encounters': count}, f)


def detect_gift_shiny(frame):
    star_roi = frame[ROI_Y:ROI_Y + ROI_H, ROI_X:ROI_X + ROI_W]
    hsv_roi = cv2.cvtColor(star_roi, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([40, 255, 255])

    mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
    yellow_pixels = cv2.countNonZero(mask)

    return yellow_pixels > 15, mask


# ==========================================
# GŁÓWNA LOGIKA
# ==========================================
def start_hunting():
    cv2.namedWindow('Nintendo Switch Stream')

    # Wczytanie licznika z JSONa
    encounters = load_counter()

    try:
        print(f"\n-> Łączenie z {PORT_COM}...")
        esp = serial.Serial(PORT_COM, 115200, timeout=0.1)
        print("-> Połączono! Inicjalizacja płytki (4 sekundy)...")
        time.sleep(4)
    except Exception as e:
        print(f"!!! BŁĄD POŁĄCZENIA Z ESP32: {e} !!!")
        esp = None

    capture_device = None
    if not TEST_MODE:
        capture_device = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        capture_device.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    state = "MASHING_A"
    phase_start_time = time.time()
    last_action_time = time.time()

    # Zmienne do bez-lagowego makra (Macro Queue)
    macro_queue = []
    next_macro_time = 0
    next_state_after_macro = ""

    mask = np.zeros((ROI_H, ROI_W), dtype=np.uint8)

    print(f"\n*** ROZPOCZĘTO ŁOWY (Obecny licznik: {encounters}) ***")

    while True:
        if not TEST_MODE:
            is_frame_read, current_frame = capture_device.read()
            if not is_frame_read:
                print("Błąd odczytu z kamery!")
                break
        else:
            if not os.path.exists(TEST_IMAGE_PATH):
                break
            current_frame = cv2.imread(TEST_IMAGE_PATH)
            current_frame = cv2.resize(current_frame, (1920, 1080))
            time.sleep(0.01)

        current_time = time.time()
        roi_color = (0, 0, 255)  # Domyślnie czerwona ramka (ślepy bot)

        # ---------------------------------------------------------
        # MASZYNA STANÓW (NAPRAWIONA)
        # ---------------------------------------------------------
        if state == "MASHING_A":
            if current_time - last_action_time > 0.6:
                if esp:
                    esp.write(b'A')
                    esp.flush()
                last_action_time = current_time

            if current_time - phase_start_time > TIME_TO_MASH_A:
                print("\n-> Koniec czasu MASHING_A. Inicjuję sekwencję otwierania...")
                macro_queue = [
                    (b'S', 1.5),
                    (b'A', 1.5),
                    (b'A', 1.5),
                    (b'A', 2.5)
                ]
                next_macro_time = current_time
                next_state_after_macro = "CHECKING_SHINY"
                state = "MACRO_EXECUTION"

        elif state == "MACRO_EXECUTION":
            if current_time >= next_macro_time:
                if len(macro_queue) > 0:
                    action, delay = macro_queue.pop(0)
                    if esp:
                        esp.write(action)
                        esp.flush()
                    next_macro_time = current_time + delay
                else:
                    # Przejście do następnego stanu
                    state = next_state_after_macro

                    # TUTAJ NAPRAWIONY BUG: Reset stopera po wyjściu z resetu gry
                    if state == "MASHING_A":
                        phase_start_time = time.time()
                        print("\n*** NOWY CYKL ***")

        elif state == "CHECKING_SHINY":
            encounters += 1
            save_counter(encounters)

            roi_color = (0, 255, 0)
            is_shiny, mask = detect_gift_shiny(current_frame)

            if is_shiny:
                print(f"\n!!! ZNALEZIONO SHINY PO {encounters} PRÓBACH !!!")
                state = "SHINY_FOUND"
            else:
                print(f"\n-> Próba {encounters}: Zwykły. Resetowanie gry...")
                macro_queue = [
                    (b'H', 1.5),
                    (b'X', 0.5),
                    (b'A', 4.0),
                    (b'A', 1.5),
                    (b'A', 12.0)
                ]
                next_macro_time = current_time
                next_state_after_macro = "MASHING_A"
                state = "MACRO_EXECUTION"

        elif state == "SHINY_FOUND":
            if esp:
                esp.write(b'Q')
                esp.flush()
            state = "STOPPED"

        elif state == "STOPPED":
            roi_color = (0, 255, 0)
            cv2.putText(current_frame, 'SHINY DETECTED! ALARM ON', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                        (0, 0, 255), 3)

        # ---------------------------------------------------------
        # WYŚWIETLANIE OBRAZU
        # ---------------------------------------------------------
        cv2.rectangle(current_frame, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), roi_color, 2)

        cv2.putText(current_frame, f'Status: {state}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(current_frame, f'Encounters: {encounters}', (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255),
                    2)

        resized_frame = cv2.resize(current_frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Nintendo Switch Stream', resized_frame)
        cv2.imshow('Yellow Mask', mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("-> Przerwano przez użytkownika.")
            break

    if capture_device:
        capture_device.release()
    if esp:
        esp.write(b'F')
        esp.close()
    cv2.destroyAllWindows()


def main():
    while True:
        print("\n" + "=" * 35)
        print("   POKEMON SHINY HUNTER BOT")
        print("=" * 35)
        print(f"Obecne Encounters: {load_counter()}")
        print("=" * 35)
        print("1. Start Gift Hunting")
        print("2. Exit")
        print("=" * 35)

        choice = input("Wybierz opcję (1/2): ")

        if choice == '1':
            start_hunting()
        elif choice == '2':
            print("Zamykanie programu...")
            sys.exit()
        else:
            print("Niepoprawna opcja. Wpisz 1 lub 2.")


if __name__ == "__main__":
    main()