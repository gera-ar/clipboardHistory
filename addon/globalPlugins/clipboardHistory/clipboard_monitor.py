# -*- coding: utf-8 -*-
# Copyright (C) 2024 Gerardo Kessler <gera.ar@yahoo.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

import api
import ctypes
from ctypes import wintypes
import threading
from .database import *

WM_CLIPBOARDUPDATE = 0x031D
ERROR_CLASS_ALREADY_EXISTS = 1410

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

try:
	LRESULT = wintypes.LRESULT
except AttributeError:
	LRESULT = ctypes.c_ssize_t

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASS(ctypes.Structure):
	"""Estructura que define las propiedades de la clase de ventana."""
	_fields_ = [
		("style", wintypes.UINT),
		("lpfnWndProc", WNDPROC),
		("cbClsExtra", ctypes.c_int),
		("cbWndExtra", ctypes.c_int),
		("hInstance", wintypes.HINSTANCE),
		("hIcon", wintypes.HANDLE),
		("hCursor", wintypes.HANDLE),
		("hbrBackground", wintypes.HANDLE),
		("lpszMenuName", wintypes.LPCWSTR),
		("lpszClassName", wintypes.LPCWSTR)
	]

class MSG(ctypes.Structure):
	"""Estructura que almacena mensajes de la cola de eventos de Windows."""
	_fields_ = [
		("hwnd", wintypes.HWND),
		("message", wintypes.UINT),
		("wParam", wintypes.WPARAM),
		("lParam", wintypes.LPARAM),
		("time", wintypes.DWORD),
		("pt", wintypes.POINT)
	]

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.GetClassInfoW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, ctypes.POINTER(WNDCLASS)]
user32.GetClassInfoW.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
	wintypes.DWORD,
	wintypes.LPCWSTR,
	wintypes.LPCWSTR,
	wintypes.DWORD,
	ctypes.c_int,
	ctypes.c_int,
	ctypes.c_int,
	ctypes.c_int,
	wintypes.HWND,
	wintypes.HMENU,
	wintypes.HINSTANCE,
	wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.AddClipboardFormatListener.argtypes = [wintypes.HWND]
user32.AddClipboardFormatListener.restype = wintypes.BOOL

user32.RemoveClipboardFormatListener.argtypes = [wintypes.HWND]
user32.RemoveClipboardFormatListener.restype = wintypes.BOOL

user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL

user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT

user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

class ClipboardMonitor:
	"""Clase para monitorear los cambios en el portapapeles de Windows."""

	def __init__(self):
		"""Inicializa la clase y prepara las estructuras necesarias."""
		self.hwnd = None
		self.msg = MSG()
		self.running = False
		self.thread = None
		self.wnd_proc_instance = WNDPROC(self.wnd_proc)

	def _registrar_clase_ventana(self, class_name, h_instance):
		"""Registra la clase de ventana o la reutiliza si ya existe."""
		wc = WNDCLASS()
		wc.lpfnWndProc = self.wnd_proc_instance
		wc.lpszClassName = class_name
		wc.hInstance = h_instance
		wc.hIcon = None
		wc.hCursor = None
		wc.hbrBackground = None
		existe = user32.GetClassInfoW(h_instance, class_name, ctypes.byref(wc))
		if existe:
			return
		atom = user32.RegisterClassW(ctypes.byref(wc))
		if atom:
			return
		err = ctypes.get_last_error()
		if err == ERROR_CLASS_ALREADY_EXISTS:
			return
		raise ctypes.WinError(err)

	def create_window(self):
		"""Crea una ventana oculta que recibe mensajes del portapapeles."""
		class_name = "ClipboardListener"
		h_instance = kernel32.GetModuleHandleW(None)
		self._registrar_clase_ventana(class_name, h_instance)
		self.hwnd = user32.CreateWindowExW(0, class_name, "Clipboard Monitor", 0, 0, 0, 0, 0, None, None, h_instance, None)
		if not self.hwnd:
			raise ctypes.WinError(ctypes.get_last_error())

	def wnd_proc(self, hwnd, msg, wParam, lParam):
		"""Procedimiento de ventana que maneja los mensajes recibidos."""
		if msg != WM_CLIPBOARDUPDATE:
			return user32.DefWindowProcW(hwnd, msg, wParam, lParam)
		try:
			content = api.getClipData()
		except OSError:
			content = None
		if not content:
			return user32.DefWindowProcW(hwnd, msg, wParam, lParam)
		rs = db.get("SELECT string, favorite FROM strings WHERE string=?", "one", (content,))
		if rs:
			db.delete("DELETE FROM strings WHERE string=?", (content,))
			favorite = rs[1]
		else:
			favorite = 0
		db.insert("INSERT INTO strings (string, favorite) VALUES (?, ?)", (content, favorite))
		counter = db.get("SELECT id FROM strings", "all")
		max_elements = db.get("SELECT max_elements FROM settings", "one")
		if max_elements and max_elements[0] != 0 and len(counter) > max_elements[0]:
			db.delete("DELETE FROM strings WHERE id=?", (counter[0][0],))
		return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

	def run(self):
		"""Cuerpo principal del monitoreo, diseñado para ejecutarse en un hilo."""
		self.create_window()
		ok = user32.AddClipboardFormatListener(self.hwnd)
		if not ok:
			raise ctypes.WinError(ctypes.get_last_error())
		self.running = True
		while self.running:
			gm = user32.GetMessageW(ctypes.byref(self.msg), self.hwnd, 0, 0)
			if gm == 0:
				break
			if gm == -1:
				raise ctypes.WinError(ctypes.get_last_error())
			user32.TranslateMessage(ctypes.byref(self.msg))
			user32.DispatchMessageW(ctypes.byref(self.msg))

	def start_monitoring(self, as_thread=False):
		"""Inicia el monitoreo del portapapeles, opcionalmente en un nuevo hilo."""
		if not as_thread:
			self.run()
			return
		self.thread = threading.Thread(target=self.run, daemon=True)
		self.thread.start()

	def stop_monitoring(self):
		"""Detiene el monitoreo del portapapeles."""
		self.running = False
		user32.PostQuitMessage(0)
		if self.hwnd:
			user32.RemoveClipboardFormatListener(self.hwnd)
		if self.thread:
			self.thread.join()
		class_name = "ClipboardListener"
		h_instance = kernel32.GetModuleHandleW(None)
		user32.UnregisterClassW(class_name, h_instance)
