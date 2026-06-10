import keyboard
import pyautogui
import pyperclip
from deep_translator import GoogleTranslator
import threading
import sys
import os
import json
from plyer import notification
import pystray
from pystray import MenuItem as item
from PIL import Image
import tkinter as tk
import re

ativo = True
idioma_origem = "pt"
tray_icon = None
CONFIG_FILE = "config.json"


# ==========================
# SUPORTE A ARQUIVOS NO EXE
# ==========================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==========================
# CONFIGURAÇÕES
# ==========================
def salvar_config():
    config = {
        "ativo": ativo,
        "idioma_origem": idioma_origem
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)


def carregar_config():
    global ativo, idioma_origem

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            ativo = config.get("ativo", True)
            idioma_origem = config.get("idioma_origem", "pt")


# ==========================
# TRADUÇÃO
# ==========================
def traduzir(texto):
    global idioma_origem

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
    global ativo

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


# ==========================
# NOTIFICAÇÃO
# ==========================
def notificar(msg):
    notification.notify(
        title="Tradutor → Chinês Simplificado",
        message=msg,
        timeout=2
    )


# ==========================
# ATIVAR / DESATIVAR
# ==========================
def alternar(icon, item):
    global ativo, tray_icon
    ativo = not ativo
    salvar_config()

    if ativo:
        tray_icon.icon = Image.open(resource_path("ico_verde.ico"))
        notificar("Tradutor Ativado ✅")
    else:
        tray_icon.icon = Image.open(resource_path("ico_vermelho.ico"))
        notificar("Tradutor Desativado ❌")


# ==========================
# DEFINIR IDIOMA
# ==========================
def definir_idioma_pt(icon, item):
    global idioma_origem
    idioma_origem = "pt"
    salvar_config()
    notificar("Idioma: Português")


def definir_idioma_en(icon, item):
    global idioma_origem
    idioma_origem = "en"
    salvar_config()
    notificar("Idioma: Inglês")


def definir_idioma_es(icon, item):
    global idioma_origem
    idioma_origem = "es"
    salvar_config()
    notificar("Idioma: Espanhol")


# ==========================
# SAIR
# ==========================
def sair(icon, item):
    icon.stop()
    sys.exit()


# ==========================
# TRAY ICON
# ==========================
def iniciar_tray():
    global tray_icon

    if ativo:
        image = Image.open(resource_path("ico_verde.ico"))
    else:
        image = Image.open(resource_path("ico_vermelho.ico"))

    menu = (
        item("Ativar / Desativar", alternar),
        item("Idioma",
             pystray.Menu(
                 item("Português", definir_idioma_pt),
                 item("Inglês", definir_idioma_en),
                 item("Espanhol", definir_idioma_es),
             )),
        item("Sair", sair)
    )

    tray_icon = pystray.Icon(
        "Tradutor",
        image,
        "Tradutor → Chinês Simplificado",
        menu
    )

    tray_icon.run()


# ==========================
# INTERFACE
# ==========================
def iniciar_interface():
    janela = tk.Tk()
    janela.title("Tradutor → Chinês Simplificado")
    janela.geometry("360x170")
    janela.resizable(False, False)

    label = tk.Label(janela, text="Shift + Enter → Traduzir")
    label.pack(pady=10)

    status_label = tk.Label(janela)
    status_label.pack()

    idioma_label = tk.Label(janela)
    idioma_label.pack(pady=5)

    def atualizar_status():
        status_label.config(
            text="Status: Ativo ✅" if ativo else "Status: Desativado ❌"
        )

        idiomas = {
            "pt": "Português",
            "en": "Inglês",
            "es": "Espanhol"
        }

        idioma_label.config(
            text=f"Idioma atual: {idiomas.get(idioma_origem, 'Desconhecido')}"
        )

        janela.after(500, atualizar_status)

    atualizar_status()
    janela.mainloop()


# ==========================
# MAIN
# ==========================
def main():
    carregar_config()

    keyboard.add_hotkey("shift+enter", traduzir_buffer, suppress=True)

    threading.Thread(target=iniciar_tray, daemon=True).start()
    iniciar_interface()


if __name__ == "__main__":
    main()