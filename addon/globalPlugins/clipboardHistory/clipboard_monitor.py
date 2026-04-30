# -*- coding: utf-8 -*-
# Copyright (C) 2024 Gerardo Kessler <gera.ar@yahoo.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

import api
import ctypes
from ctypes import wintypes
import threading
import os
import time
import struct
import hashlib
import logHandler
from .database import *
import addonHandler

addonHandler.initTranslation()

WM_CLIPBOARDUPDATE = 0x031D
ERROR_CLASS_ALREADY_EXISTS = 1410

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)

# Constantes del Portapapeles
CF_TEXT = 1
CF_DIB = 8
CF_UNICODETEXT = 13
CF_HDROP = 15
CF_DIBV5 = 17

# Firmas WinAPI para 64 bits
try:
	LRESULT = wintypes.LRESULT
except AttributeError:
	LRESULT = ctypes.c_ssize_t

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL
user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.c_void_p]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND

kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalSize.argtypes = [wintypes.HANDLE]
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HANDLE
kernel32.GlobalFree.argtypes = [wintypes.HANDLE]
kernel32.GlobalFree.restype = wintypes.HANDLE

shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
shell32.DragQueryFileW.restype = wintypes.UINT

class WNDCLASS(ctypes.Structure):
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
	_fields_ = [
		("hwnd", wintypes.HWND),
		("message", wintypes.UINT),
		("wParam", wintypes.WPARAM),
		("lParam", wintypes.LPARAM),
		("time", wintypes.DWORD),
		("pt", wintypes.POINT)
	]

class ClipboardMonitor:
	def __init__(self):
		self.hwnd = None
		self.msg = MSG()
		self.running = False
		self.thread = None
		self.wnd_proc_instance = WNDPROC(self.wnd_proc)

	def create_window(self):
		class_name = "ClipboardListener"
		h_instance = kernel32.GetModuleHandleW(None)
		wc = WNDCLASS()
		wc.lpfnWndProc = self.wnd_proc_instance
		wc.lpszClassName = class_name
		wc.hInstance = h_instance
		user32.RegisterClassW(ctypes.byref(wc))
		self.hwnd = user32.CreateWindowExW(0, class_name, "Clipboard Monitor", 0, 0, 0, 0, 0, None, None, h_instance, None)

	def wnd_proc(self, hwnd, msg, wParam, lParam):
		if msg != WM_CLIPBOARDUPDATE:
			return user32.DefWindowProcW(hwnd, msg, wParam, lParam)
		try:
			import globalVars
			media_dir = os.path.join(globalVars.appArgs.configPath, 'clipboard_history_media')
			content = self.get_content(media_dir)
			if content:
				type_val, string_val, data_val = content
				
				# Buscamos duplicados por contenido real (data_val). Si es type 0 (texto), data_val contiene el texto real
				rs = db.get("SELECT favorite, string FROM strings WHERE type=? AND data=?", "one", (type_val, data_val))
				if rs:
					# Recuperamos el estado de favorito y el nombre personalizado (etiqueta) que tenía
					favorite, string_val = rs[0], rs[1]
					db.delete("DELETE FROM strings WHERE type=? AND data=?", (type_val, data_val))
				else:
					# Compatibilidad con elementos de texto antiguos donde data era NULL
					if type_val == 0:
						rs_old = db.get("SELECT favorite, string FROM strings WHERE type=0 AND string=? AND data IS NULL", "one", (string_val,))
						if rs_old:
							favorite, string_val = rs_old[0], rs_old[1]
							db.delete("DELETE FROM strings WHERE type=0 AND string=? AND data IS NULL", (string_val,))
						else:
							favorite = 0
					else:
						favorite = 0
						
				db.insert("INSERT INTO strings (string, favorite, type, data) VALUES (?, ?, ?, ?)", (string_val, favorite, type_val, data_val))
				self._cleanup_old_entries(media_dir)
		except Exception as e:
			logHandler.log.error(f"Error en ClipboardMonitor: {e}")
		return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

	def _cleanup_old_entries(self, media_dir):
		counter = db.get("SELECT id FROM strings ORDER BY id ASC", "all")
		max_elements = db.get("SELECT max_elements FROM settings", "one")
		if max_elements and max_elements[0] != 0 and len(counter) > max_elements[0]:
			oldest_id = counter[0][0]
			oldest_info = db.get("SELECT type, data FROM strings WHERE id=?", "one", (oldest_id,))
			db.delete("DELETE FROM strings WHERE id=?", (oldest_id,))
			if oldest_info and oldest_info[0] == 2 and oldest_info[1]:
				path = os.path.join(media_dir, oldest_info[1])
				if os.path.exists(path):
					try: os.remove(path)
					except: pass

	def get_content(self, media_dir):
		opened = False
		# Usamos i en lugar de _ para evitar pisar la función de traducción
		for i in range(5):
			if user32.OpenClipboard(None):
				opened = True
				break
			time.sleep(0.05)
		if not opened: return None
		try:
			# 1. Archivos
			if user32.IsClipboardFormatAvailable(CF_HDROP):
				h = user32.GetClipboardData(CF_HDROP)
				if h:
					count = shell32.DragQueryFileW(h, 0xFFFFFFFF, None, 0)
					files = []
					for i_file in range(count):
						length = shell32.DragQueryFileW(h, i_file, None, 0)
						buf = ctypes.create_unicode_buffer(length + 1)
						shell32.DragQueryFileW(h, i_file, buf, length + 1)
						if buf.value: files.append(buf.value)
					if files:
						data = "|".join(files)
						name = os.path.basename(files[0]) if len(files) == 1 else _("{} archivos: {}...").format(len(files), os.path.basename(files[0]))
						return (1, name, data)
			# 2. Imágenes
			img_fmt = CF_DIBV5 if user32.IsClipboardFormatAvailable(CF_DIBV5) else (CF_DIB if user32.IsClipboardFormatAvailable(CF_DIB) else 0)
			if img_fmt:
				h = user32.GetClipboardData(img_fmt)
				if h:
					ptr = kernel32.GlobalLock(h)
					size = kernel32.GlobalSize(h)
					if ptr and size:
						raw = ctypes.string_at(ptr, size)
						kernel32.GlobalUnlock(h)
						h_img = hashlib.md5(raw).hexdigest()
						fname = f"{h_img}.bmp"
						if not os.path.exists(media_dir): os.makedirs(media_dir)
						path = os.path.join(media_dir, fname)
						if os.path.exists(path) or self._save_bmp(raw, path):
							import datetime
							timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
							return (2, _("Imagen copiada ({})").format(timestamp), fname)
					elif ptr: kernel32.GlobalUnlock(h)
			# 3. Texto
			text = None
			if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
				h = user32.GetClipboardData(CF_UNICODETEXT)
				if h:
					ptr = kernel32.GlobalLock(h)
					if ptr:
						text = ctypes.wstring_at(ptr)
						kernel32.GlobalUnlock(h)
			elif user32.IsClipboardFormatAvailable(CF_TEXT):
				h = user32.GetClipboardData(CF_TEXT)
				if h:
					ptr = kernel32.GlobalLock(h)
					if ptr:
						text = ctypes.string_at(ptr).decode('mbcs', errors='replace')
						kernel32.GlobalUnlock(h)
			if text and text.strip(): return (0, text, text)
		finally: user32.CloseClipboard()
		return None

	def _save_bmp(self, data, path):
		try:
			if len(data) < 40: return False
			sz = struct.unpack_from('<I', data)[0]
			if sz == 12:
				bits = struct.unpack_from('<H', data, 10)[0]
				off = 14 + sz + ((1 << bits) if bits <= 8 else 0) * 3
			else:
				bits = struct.unpack_from('<H', data, 14)[0]
				comp = struct.unpack_from('<I', data, 16)[0]
				clr = struct.unpack_from('<I', data, 32)[0]
				pal = (clr if clr > 0 else (1 << bits if bits <= 8 else 0)) * 4
				if bits > 8 and comp == 3: pal = 12
				off = 14 + sz + pal
			head = struct.pack('<2sIHHI', b'BM', 14 + len(data), 0, 0, off)
			with open(path, 'wb') as f:
				f.write(head)
				f.write(data)
			return True
		except: return False

	def set_files(self, paths):
		class DROPFILES(ctypes.Structure):
			_fields_ = [("pFiles", wintypes.DWORD), ("pt", wintypes.POINT), ("fNC", wintypes.BOOL), ("fWide", wintypes.BOOL)]
		buf = "\0".join(paths) + "\0\0"
		b_bytes = buf.encode('utf-16le')
		size = ctypes.sizeof(DROPFILES) + len(b_bytes)
		h = kernel32.GlobalAlloc(0x0042, size)
		if not h: return False
		ptr = kernel32.GlobalLock(h)
		df = DROPFILES(pFiles=ctypes.sizeof(DROPFILES), fNC=0, fWide=1)
		ctypes.memmove(ptr, ctypes.byref(df), ctypes.sizeof(DROPFILES))
		ctypes.memmove(ptr + ctypes.sizeof(DROPFILES), b_bytes, len(b_bytes))
		kernel32.GlobalUnlock(h)
		if user32.OpenClipboard(None):
			user32.EmptyClipboard()
			user32.SetClipboardData(CF_HDROP, h)
			user32.CloseClipboard()
			return True
		kernel32.GlobalFree(h)
		return False

	def set_image(self, path):
		try:
			with open(path, 'rb') as f: d = f.read()
			if not d.startswith(b'BM'): return False
			raw = d[14:]
			h = kernel32.GlobalAlloc(0x0042, len(raw))
			if not h: return False
			ptr = kernel32.GlobalLock(h)
			ctypes.memmove(ptr, raw, len(raw))
			kernel32.GlobalUnlock(h)
			if user32.OpenClipboard(None):
				user32.EmptyClipboard()
				user32.SetClipboardData(CF_DIB, h)
				user32.CloseClipboard()
				return True
			kernel32.GlobalFree(h)
			return False
		except: return False

	def run(self):
		self.create_window()
		if not user32.AddClipboardFormatListener(self.hwnd): return
		self.running = True
		while self.running:
			if user32.GetMessageW(ctypes.byref(self.msg), self.hwnd, 0, 0) <= 0: break
			user32.TranslateMessage(ctypes.byref(self.msg))
			user32.DispatchMessageW(ctypes.byref(self.msg))

	def start_monitoring(self, as_thread=False):
		if not as_thread:
			self.run()
			return
		self.thread = threading.Thread(target=self.run, daemon=True)
		self.thread.start()

	def stop_monitoring(self):
		self.running = False
		user32.PostQuitMessage(0)
		if self.hwnd: user32.RemoveClipboardFormatListener(self.hwnd)
