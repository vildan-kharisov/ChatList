#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовая программа для просмотра и редактирования SQLite баз данных
"""

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QTextEdit, QLabel, QDialogButtonBox, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt
from typing import Optional, List, Dict, Any


class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = None
        self.connection = None
        self.current_table = None
        self.current_page = 0
        self.page_size = 50
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Просмотр SQLite базы данных')
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Левая панель: список таблиц
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Кнопка выбора файла БД
        self.select_db_btn = QPushButton('Выбрать базу данных')
        self.select_db_btn.clicked.connect(self.select_database)
        left_layout.addWidget(self.select_db_btn)
        
        # Список таблиц
        self.tables_list = QListWidget()
        self.tables_list.itemClicked.connect(self.on_table_selected)
        left_layout.addWidget(self.tables_list)
        
        # Кнопка "Открыть"
        self.open_table_btn = QPushButton('Открыть')
        self.open_table_btn.setEnabled(False)
        self.open_table_btn.clicked.connect(self.open_table)
        left_layout.addWidget(self.open_table_btn)
        
        left_panel.setMaximumWidth(250)
        main_layout.addWidget(left_panel)
        
        # Правая панель: таблица данных
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Информация о таблице
        self.table_info_label = QLabel('Выберите базу данных и таблицу')
        right_layout.addWidget(self.table_info_label)
        
        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.data_table)
        
        # Панель пагинации и CRUD
        controls_layout = QVBoxLayout()
        
        # Пагинация
        pagination_layout = QHBoxLayout()
        self.page_info_label = QLabel('')
        pagination_layout.addWidget(self.page_info_label)
        
        self.prev_page_btn = QPushButton('◀ Предыдущая')
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.next_page_btn = QPushButton('Следующая ▶')
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_page_btn)
        
        pagination_layout.addStretch()
        
        page_size_layout = QHBoxLayout()
        page_size_layout.addWidget(QLabel('Записей на странице:'))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setMinimum(10)
        self.page_size_spin.setMaximum(500)
        self.page_size_spin.setValue(50)
        self.page_size_spin.valueChanged.connect(self.on_page_size_changed)
        page_size_layout.addWidget(self.page_size_spin)
        pagination_layout.addLayout(page_size_layout)
        
        controls_layout.addLayout(pagination_layout)
        
        # CRUD кнопки
        crud_layout = QHBoxLayout()
        
        self.create_btn = QPushButton('Создать')
        self.create_btn.clicked.connect(self.create_record)
        self.create_btn.setEnabled(False)
        crud_layout.addWidget(self.create_btn)
        
        self.update_btn = QPushButton('Изменить')
        self.update_btn.clicked.connect(self.update_record)
        self.update_btn.setEnabled(False)
        crud_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton('Удалить')
        self.delete_btn.clicked.connect(self.delete_record)
        self.delete_btn.setEnabled(False)
        crud_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton('Обновить')
        self.refresh_btn.clicked.connect(self.refresh_table)
        self.refresh_btn.setEnabled(False)
        crud_layout.addWidget(self.refresh_btn)
        
        crud_layout.addStretch()
        
        controls_layout.addLayout(crud_layout)
        
        right_layout.addLayout(controls_layout)
        
        main_layout.addWidget(right_panel, 1)
    
    def select_database(self):
        """Выбор файла базы данных"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Выбрать базу данных', '', 'SQLite Files (*.db *.sqlite *.sqlite3)')
        
        if filename:
            try:
                self.db_path = filename
                self.connection = sqlite3.connect(filename)
                self.connection.row_factory = sqlite3.Row
                self.load_tables()
                self.table_info_label.setText(f'База данных: {filename}')
                QMessageBox.information(self, 'Успех', 'База данных загружена')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть базу данных:\n{e}')
    
    def load_tables(self):
        """Загрузка списка таблиц"""
        if not self.connection:
            return
        
        self.tables_list.clear()
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            self.tables_list.addItem(table[0])
        
        self.open_table_btn.setEnabled(len(tables) > 0)
    
    def on_table_selected(self, item):
        """Обработчик выбора таблицы"""
        self.current_table = item.text()
        self.open_table_btn.setEnabled(True)
    
    def open_table(self):
        """Открытие таблицы с пагинацией"""
        if not self.current_table or not self.connection:
            return
        
        self.current_page = 0
        self.load_table_data()
    
    def load_table_data(self):
        """Загрузка данных таблицы с пагинацией"""
        if not self.current_table or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Получение общего количества записей
            cursor.execute(f"SELECT COUNT(*) FROM {self.current_table}")
            total_records = cursor.fetchone()[0]
            
            # Получение структуры таблицы
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # Вычисление пагинации
            total_pages = (total_records + self.page_size - 1) // self.page_size if total_records > 0 else 1
            offset = self.current_page * self.page_size
            
            # Загрузка данных с пагинацией
            cursor.execute(f"SELECT * FROM {self.current_table} LIMIT ? OFFSET ?", 
                          (self.page_size, offset))
            rows = cursor.fetchall()
            
            # Настройка таблицы
            self.data_table.setColumnCount(len(column_names))
            self.data_table.setHorizontalHeaderLabels(column_names)
            self.data_table.setRowCount(len(rows))
            
            # Заполнение данных
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else '')
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Только для чтения
                    self.data_table.setItem(i, j, item)
            
            # Обновление информации о странице
            start_record = offset + 1 if total_records > 0 else 0
            end_record = min(offset + self.page_size, total_records)
            self.page_info_label.setText(
                f'Страница {self.current_page + 1} из {total_pages} '
                f'(записи {start_record}-{end_record} из {total_records})')
            
            # Обновление кнопок пагинации
            self.prev_page_btn.setEnabled(self.current_page > 0)
            self.next_page_btn.setEnabled(self.current_page < total_pages - 1)
            
            # Включение CRUD кнопок
            self.create_btn.setEnabled(True)
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            
            self.table_info_label.setText(f'Таблица: {self.current_table} | Всего записей: {total_records}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить данные:\n{e}')
    
    def prev_page(self):
        """Переход на предыдущую страницу"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Переход на следующую страницу"""
        self.current_page += 1
        self.load_table_data()
    
    def on_page_size_changed(self, value):
        """Обработчик изменения размера страницы"""
        self.page_size = value
        self.current_page = 0
        if self.current_table:
            self.load_table_data()
    
    def create_record(self):
        """Создание новой записи"""
        if not self.current_table or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            
            dialog = RecordDialog(self, columns_info, None)
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.get_values()
                if values:
                    columns = [col[1] for col in columns_info if col[1] in values]
                    placeholders = ', '.join(['?' for _ in columns])
                    column_names = ', '.join(columns)
                    sql = f"INSERT INTO {self.current_table} ({column_names}) VALUES ({placeholders})"
                    cursor.execute(sql, [values[col] for col in columns])
                    self.connection.commit()
                    QMessageBox.information(self, 'Успех', 'Запись создана')
                    self.load_table_data()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось создать запись:\n{e}')
            if self.connection:
                self.connection.rollback()
    
    def update_record(self):
        """Изменение выбранной записи"""
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите строку для изменения')
            return
        
        row = selected_rows[0].row()
        if not self.current_table or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            
            # Получение текущих значений
            current_values = {}
            for j, col_info in enumerate(columns_info):
                item = self.data_table.item(row, j)
                if item:
                    current_values[col_info[1]] = item.text()
            
            # Получение первичного ключа
            pk_column = None
            for col_info in columns_info:
                if col_info[5] == 1:  # pk flag
                    pk_column = col_info[1]
                    break
            
            if not pk_column:
                QMessageBox.warning(self, 'Предупреждение', 'Таблица не имеет первичного ключа')
                return
            
            pk_value = current_values.get(pk_column)
            
            dialog = RecordDialog(self, columns_info, current_values)
            if dialog.exec_() == QDialog.Accepted:
                new_values = dialog.get_values()
                if new_values:
                    set_clause = ', '.join([f"{col} = ?" for col in new_values.keys()])
                    sql = f"UPDATE {self.current_table} SET {set_clause} WHERE {pk_column} = ?"
                    params = list(new_values.values()) + [pk_value]
                    cursor.execute(sql, params)
                    self.connection.commit()
                    QMessageBox.information(self, 'Успех', 'Запись обновлена')
                    self.load_table_data()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить запись:\n{e}')
            if self.connection:
                self.connection.rollback()
    
    def delete_record(self):
        """Удаление выбранной записи"""
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите строку для удаления')
            return
        
        row = selected_rows[0].row()
        if not self.current_table or not self.connection:
            return
        
        reply = QMessageBox.question(
            self, 'Подтверждение', 'Удалить выбранную запись?',
            QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            
            # Получение первичного ключа
            pk_column = None
            for col_info in columns_info:
                if col_info[5] == 1:  # pk flag
                    pk_column = col_info[1]
                    break
            
            if not pk_column:
                QMessageBox.warning(self, 'Предупреждение', 'Таблица не имеет первичного ключа')
                return
            
            # Получение значения первичного ключа
            pk_index = next((i for i, col in enumerate(columns_info) if col[1] == pk_column), None)
            if pk_index is None:
                return
            
            pk_item = self.data_table.item(row, pk_index)
            if not pk_item:
                return
            
            pk_value = pk_item.text()
            
            sql = f"DELETE FROM {self.current_table} WHERE {pk_column} = ?"
            cursor.execute(sql, (pk_value,))
            self.connection.commit()
            QMessageBox.information(self, 'Успех', 'Запись удалена')
            self.load_table_data()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить запись:\n{e}')
            if self.connection:
                self.connection.rollback()
    
    def refresh_table(self):
        """Обновление данных таблицы"""
        if self.current_table:
            self.load_table_data()
    
    def closeEvent(self, event):
        """Закрытие соединения с БД при закрытии окна"""
        if self.connection:
            self.connection.close()
        event.accept()


class RecordDialog(QDialog):
    """Диалог для создания/редактирования записи"""
    def __init__(self, parent=None, columns_info=None, current_values=None):
        super().__init__(parent)
        self.columns_info = columns_info or []
        self.current_values = current_values or {}
        self.setWindowTitle('Редактирование записи' if current_values else 'Создание записи')
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        self.inputs = {}
        
        for col_info in self.columns_info:
            col_name = col_info[1]
            col_type = col_info[2]
            is_pk = col_info[5] == 1
            
            # Пропускаем AUTOINCREMENT поля при создании
            if not self.current_values and is_pk and 'INTEGER' in col_type.upper():
                continue
            
            if 'TEXT' in col_type.upper() or 'VARCHAR' in col_type.upper():
                if col_name in self.current_values and len(str(self.current_values[col_name])) > 100:
                    # Для длинных текстов используем QTextEdit
                    input_widget = QTextEdit()
                    input_widget.setPlainText(self.current_values.get(col_name, ''))
                    input_widget.setMaximumHeight(100)
                else:
                    input_widget = QLineEdit()
                    input_widget.setText(self.current_values.get(col_name, ''))
            elif 'INTEGER' in col_type.upper():
                input_widget = QLineEdit()
                input_widget.setText(str(self.current_values.get(col_name, '')))
            else:
                input_widget = QLineEdit()
                input_widget.setText(str(self.current_values.get(col_name, '')))
            
            if is_pk and self.current_values:
                input_widget.setEnabled(False)  # Первичный ключ нельзя изменять
            
            self.inputs[col_name] = input_widget
            form_layout.addRow(f'{col_name}:', input_widget)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        """Получение значений из формы"""
        values = {}
        for col_name, widget in self.inputs.items():
            if isinstance(widget, QTextEdit):
                value = widget.toPlainText()
            else:
                value = widget.text()
            
            if value.strip() or col_name in self.current_values:
                values[col_name] = value.strip() if value.strip() else None
        return values


def main():
    app = QApplication(sys.argv)
    window = DatabaseViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
