import keyboard
import pyautogui
import pyperclip
from deep_translator import GoogleTranslator
import threading
import sys
import os
import json
from datetime import datetime
from plyer import notification
import pystray
from pystray import MenuItem as item
from PIL import Image
import tkinter as tk
import re

APP_NAME = "LiveTextTranslator"

APPDATA_PATH = os.path.join(os.getenv("APPDATA"), APP_NAME)
os.makedirs(APPDATA_PATH, exist_ok=True)

CONFIG_FILE = os.path.join(APPDATA_PATH, "config.json")
HISTORY_FILE = os.path.join(APPDATA_PATH, "history.json")

ativo = True
idioma_origem = "auto"
hotkey_configurada = "shift+enter"
tray_icon = None


# ==========================
# SUPORTE EXE
# ==========================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==========================
# CONFIG
# ==========================
def salvar_config():
    config = {
        "ativo": ativo,
        "idioma_origem": idioma_origem,
        "hotkey": hotkey_configurada
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def carregar_config():
    global ativo, idioma_origem, hotkey_configurada

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            ativo = config.get("ativo", True)
            idioma_origem = config.get("idioma_origem", "auto")
            hotkey_configurada = config.get("hotkey", "shift+enter")


# ==========================
# HISTÓRICO
# ==========================
def salvar_historico(original, traducao):
    registro = {
        "original": original,
        "traducao": traducao,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    historico = []

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            historico = json.load(f)

    historico.insert(0, registro)
    historico = historico[:100]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=4)


# ==========================
# TRADUÇÃO
# ==========================
def traduzir(texto):
    try:
        texto = texto.strip()

        match = re.match(r"^(.*?)([.,!?…]+)?$", texto)
        conteudo = match.group(1)
        pontuacao = match.group(2) if match.group(2) else ""

        traducao = GoogleTranslator(
            source=idioma_origem,
            target="zh-CN"
        ).translate(conteudo)

        traducao_limpa = ""

        for c in traducao:
            if '\u4e00' <= c <= '\u9fff':
                traducao_limpa += c
            elif not c.isalpha():
                traducao_limpa += c

        return traducao_limpa + pontuacao

    except:
        return texto


# ==========================
# TRADUZIR LINHA
# ==========================
def traduzir_buffer():
    if not ativo:
        return

    pyautogui.sleep(0.05)
    pyautogui.hotkey("shift", "home")
    pyautogui.sleep(0.05)
    pyautogui.hotkey("ctrl", "c")

    texto = pyperclip.paste().strip()
    if texto == "":
        return

    traducao = traduzir(texto)

    pyautogui.press("backspace")
    pyperclip.copy(traducao)
    pyautogui.hotkey("ctrl", "v")

    salvar_historico(texto, traducao)


# ==========================
# HOTKEY DINÂMICA
# ==========================
def atualizar_hotkey(nova_hotkey):
    global hotkey_configurada
    keyboard.clear_all_hotkeys()
    hotkey_configurada = nova_hotkey
    keyboard.add_hotkey(hotkey_configurada, traduzir_buffer, suppress=True)
    salvar_config()
    notificar(f"Hotkey alterada para {nova_hotkey}")


# ==========================
# NOTIFICAÇÃO
# ==========================
def notificar(msg):
    notification.notify(
        title="Live Text Translator v1.1.0",
        message=msg,
        timeout=2
    )


# ==========================
# HISTÓRICO UI
# ==========================
def abrir_historico():
    if not os.path.exists(HISTORY_FILE):
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        historico = json.load(f)

    janela = tk.Toplevel()
    janela.title("Histórico")
    janela.geometry("500x400")

    texto_area = tk.Text(janela)
    texto_area.pack(fill="both", expand=True)

    for item in historico:
        texto_area.insert("end", f"{item['data']}\n")
        texto_area.insert("end", f"Original: {item['original']}\n")
        texto_area.insert("end", f"Tradução: {item['traducao']}\n")
        texto_area.insert("end", "-"*40 + "\n")


# ==========================
# ATIVAR
# ==========================
def alternar():
    global ativo
    ativo = not ativo
    salvar_config()
    notificar("Ativado ✅" if ativo else "Desativado ❌")


# ==========================
# TRAY
# ==========================
def iniciar_tray():
    image = Image.open(resource_path("ico_verde.ico"))

    menu = (
        item("Ativar / Desativar", lambda icon, item: alternar()),
        item("Histórico", lambda icon, item: abrir_historico()),
        item("Hotkey Shift+Enter", lambda icon, item: atualizar_hotkey("shift+enter")),
        item("Hotkey Ctrl+Alt+T", lambda icon, item: atualizar_hotkey("ctrl+alt+t")),
        item("Sair", lambda icon, item: sys.exit())
    )

    tray = pystray.Icon("LiveTranslator", image, "Live Text Translator", menu)
    tray.run()


# ==========================
# MAIN
# ==========================
def main():
    carregar_config()

    keyboard.add_hotkey(hotkey_configurada, traduzir_buffer, suppress=True)

    threading.Thread(target=iniciar_tray, daemon=True).start()

    root = tk.Tk()
    root.title("Live Text Translator v1.1.0")
    root.geometry("300x120")
    tk.Label(root, text="Tradutor ativo.\nUse hotkey configurada.").pack(pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()