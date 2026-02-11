# -*- coding: utf-8 -*-
# Copyright (C) 2024 Gerardo Kessler <gera.ar@yahoo.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

import api
import globalVars
root_path= globalVars.appArgs.configPath
import os
import sys
dirAddon= os.path.dirname(__file__)
sys.path.append(dirAddon)
sys.path.append(os.path.join(dirAddon, "lib"))
if sys.version.startswith("3.11"):
	sys.path.append(os.path.join(dirAddon, "lib", "_311"))
	from .lib._311 import sqlite3 as sql
	sql.__path__.append(os.path.join(dirAddon, "lib", "_311", "sqlite3"))
elif sys.version.startswith("3.13"):
	sys.path.append(os.path.join(dirAddon, "lib", "_313"))
	from .lib._313 import sqlite3 as sql
	sql.__path__.append(os.path.join(dirAddon, "lib", "_313", "sqlite3"))
else:
	sys.path.append(os.path.join(dirAddon, "lib", "_37"))
	from .lib._37 import sqlite3 as sql
	sql.__path__.append(os.path.join(dirAddon, "lib", "_37", "sqlite3"))
del sys.path[-3:]
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

class DB:
	def __init__(self):
		self.connect= sql.connect(os.path.join(root_path, 'clipboard_history'), check_same_thread= False)
		self.cursor= self.connect.cursor()
		self.cursor.execute('PRAGMA TABLE_INFO(strings)')
		if len(self.cursor.fetchall()) == 0:
			self.initialStructure()
		else:
			self.cursor.execute('VACUUM')
			self.connect.commit()

	def initialStructure(self):
		self.cursor.execute('CREATE TABLE strings (string TEXT, favorite BOOLEAN, id INTEGER PRIMARY KEY AUTOINCREMENT)')
		self.cursor.execute('CREATE TABLE settings (sounds BOOLEAN, max_elements INTEGER, number BOOLEAN)')
		# Translators: Cadena para la base de datos inicial con un texto de prueba
		new_content= _('Texto de prueba')
		try:
			new_content= api.getClipData()
		except OSError:
			pass
		self.cursor.execute('INSERT INTO strings (string, favorite) VALUES (?, ?)', (new_content, 0))
		self.cursor.execute('INSERT INTO settings (sounds, max_elements, number) VALUES (1, 250, 1)')
		self.connect.commit()

	def insert(self, query, values):
		self.cursor.execute(query, values)
		self.connect.commit()

	def get(self, query, fetch, values=None):
		if values:
			self.cursor.execute(query, values)
		else:
			self.cursor.execute(query)
		if fetch == 'all':
			return self.cursor.fetchall()
		elif fetch == 'one':
			return self.cursor.fetchone()

	def update(self, query, values):
		self.cursor.execute(query, values)
		self.connect.commit()

	def delete(self, query, values=None):
		if values:
			self.cursor.execute(query, values)
		else:
			self.cursor.execute(query)
		self.connect.commit()

	def many(self, query, values):
		self.cursor.executemany(query, values)
		self.connect.commit()

db= DB()