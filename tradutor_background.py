import keyboard
import pyautogui
import pyperclip
from deep_translator import GoogleTranslator
import deepl
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

# ==========================
# CONFIGURAÇÃO DE APPDATA
# ==========================
APP_NAME = "LiveTextTranslator"
APPDATA_PATH = os.path.join(os.getenv("APPDATA"), APP_NAME)
os.makedirs(APPDATA_PATH, exist_ok=True)

CONFIG_FILE = os.path.join(APPDATA_PATH, "config.json")
HISTORY_FILE = os.path.join(APPDATA_PATH, "history.json")

# ==========================
# VARIÁVEIS GLOBAIS
# ==========================
ativo = True
idioma_origem = "auto"
hotkey_configurada = "shift+enter"
motor_traducao = "google"
deepl_api_key = ""

tray_icon = None


# ==========================
# SUPORTE A EXECUTÁVEL
# ==========================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==========================
# CONFIGURAÇÃO
# ==========================
def salvar_config():
    config = {
        "ativo": ativo,
        "idioma_origem": idioma_origem,
        "hotkey": hotkey_configurada,
        "motor_traducao": motor_traducao,
        "deepl_api_key": deepl_api_key
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def carregar_config():
    global ativo, idioma_origem, hotkey_configurada
    global motor_traducao, deepl_api_key

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            ativo = config.get("ativo", True)
            idioma_origem = config.get("idioma_origem", "auto")
            hotkey_configurada = config.get("hotkey", "shift+enter")
            motor_traducao = config.get("motor_traducao", "google")
            deepl_api_key = config.get("deepl_api_key", "")


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
    global motor_traducao, deepl_api_key

    texto = texto.strip()

    match = re.match(r"^(.*?)([.,!?…]+)?$", texto)
    conteudo = match.group(1)
    pontuacao = match.group(2) if match.group(2) else ""

    try:
        # 🔵 DeepL
        if motor_traducao == "deepl" and deepl_api_key:
            translator = deepl.Translator(deepl_api_key)
            result = translator.translate_text(conteudo, target_lang="ZH")
            traducao = result.text
        else:
            # 🟢 Google
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
        # fallback automático
        try:
            traducao = GoogleTranslator(
                source=idioma_origem,
                target="zh-CN"
            ).translate(conteudo)
            return traducao + pontuacao
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
# MOTOR DE TRADUÇÃO
# ==========================
def usar_google(icon=None, item=None):
    global motor_traducao
    motor_traducao = "google"
    salvar_config()
    notificar("Motor: Google")


def usar_deepl(icon=None, item=None):
    global motor_traducao
    if not deepl_api_key:
        notificar("Adicione API DeepL primeiro")
        return
    motor_traducao = "deepl"
    salvar_config()
    notificar("Motor: DeepL")


# ==========================
# INSERIR API
# ==========================
def inserir_api_deepl():
    global deepl_api_key

    janela = tk.Toplevel()
    janela.title("Inserir API DeepL")
    janela.geometry("400x150")

    tk.Label(janela, text="Cole sua API Key DeepL:").pack(pady=5)

    entrada = tk.Entry(janela, width=50)
    entrada.pack(pady=5)

    def salvar():
        global deepl_api_key
        deepl_api_key = entrada.get().strip()
        salvar_config()
        notificar("API DeepL salva")
        janela.destroy()

    tk.Button(janela, text="Salvar", command=salvar).pack(pady=5)


# ==========================
# NOTIFICAÇÃO
# ==========================
def notificar(msg):
    notification.notify(
        title="Live Text Translator v1.2.0",
        message=msg,
        timeout=2
    )


# ==========================
# TRAY ICON
# ==========================
def iniciar_tray():
    image = Image.open(resource_path("ico_verde.ico"))

    menu = (
        item("Motor Google", usar_google),
        item("Motor DeepL", usar_deepl),
        item("Inserir API DeepL", lambda icon, item: inserir_api_deepl()),
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
    root.title("Live Text Translator v1.2.0")
    root.geometry("320x140")
    tk.Label(root, text="Motor selecionável (Google / DeepL)").pack(pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()