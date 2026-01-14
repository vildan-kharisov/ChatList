#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основное приложение ChatList - GUI интерфейс
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QLabel, QMessageBox, QProgressBar, QGroupBox, QSplitter,
    QHeaderView, QMenuBar, QMenu, QStatusBar, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QStyledItemDelegate
)
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import List, Dict, Optional
import db
import models
import network


class RequestWorker(QThread):
    """Рабочий поток для асинхронной отправки запросов"""
    finished = pyqtSignal(int, dict)  # model_id, результат
    
    def __init__(self, model, prompt, timeout):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.timeout = timeout
    
    def run(self):
        result = network.send_request(self.model, self.prompt, self.timeout)
        self.finished.emit(self.model.id, result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.temp_results = []  # Временная таблица результатов в памяти
        self.current_prompt_id = None
        self.workers = []  # Список активных потоков
        self.init_database()
        self.init_ui()
        self.load_prompts()
        self.load_models()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            db.init_database()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка БД', f'Не удалось инициализировать БД: {e}')
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('ChatList - Сравнение ответов нейросетей')
        self.setGeometry(100, 100, 1200, 800)
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Меню
        self.create_menu()
        
        # Область ввода промта
        prompt_group = self.create_prompt_area()
        main_layout.addWidget(prompt_group)
        
        # Область выбора моделей
        models_group = self.create_models_area()
        main_layout.addWidget(models_group)
        
        # Разделитель для области результатов
        splitter = QSplitter(Qt.Vertical)
        
        # Таблица результатов
        results_group = self.create_results_area()
        splitter.addWidget(results_group)
        
        # Кнопки управления
        buttons_layout = self.create_buttons_area()
        splitter.addWidget(buttons_layout)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(splitter, 1)
        
        # Статус-бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Готово')
    
    def create_menu(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        file_menu.addAction('Управление промтами', self.show_prompts_window)
        file_menu.addAction('Управление моделями', self.show_models_window)
        file_menu.addAction('Сохраненные результаты', self.show_results_window)
        file_menu.addSeparator()
        file_menu.addAction('Выход', self.close)
        
        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        help_menu.addAction('О программе', self.show_about)
    
    def create_prompt_area(self) -> QGroupBox:
        """Создание области ввода промта"""
        group = QGroupBox('Промт')
        layout = QVBoxLayout()
        
        # Выбор сохраненного промта
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel('Выбрать сохраненный промт:'))
        self.prompt_combo = QComboBox()
        self.prompt_combo.currentIndexChanged.connect(self.on_prompt_selected)
        h_layout.addWidget(self.prompt_combo, 1)
        layout.addLayout(h_layout)
        
        # Поле ввода нового промта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText('Введите промт или выберите из списка...')
        self.prompt_input.setMaximumHeight(100)
        layout.addWidget(self.prompt_input)
        
        group.setLayout(layout)
        return group
    
    def create_models_area(self) -> QGroupBox:
        """Создание области выбора моделей"""
        group = QGroupBox('Модели')
        layout = QVBoxLayout()
        
        # Кнопки выбора
        buttons_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('Выбрать все')
        self.select_all_btn.clicked.connect(self.select_all_models)
        self.deselect_all_btn = QPushButton('Снять все')
        self.deselect_all_btn.clicked.connect(self.deselect_all_models)
        buttons_layout.addWidget(self.select_all_btn)
        buttons_layout.addWidget(self.deselect_all_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Контейнер для чекбоксов моделей
        self.models_container = QWidget()
        self.models_layout = QHBoxLayout()
        self.models_layout.setAlignment(Qt.AlignLeft)
        self.models_container.setLayout(self.models_layout)
        layout.addWidget(self.models_container)
        
        group.setLayout(layout)
        return group
    
    def create_results_area(self) -> QGroupBox:
        """Создание области результатов"""
        group = QGroupBox('Результаты')
        layout = QVBoxLayout()
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(['Выбрано', 'Модель', 'Ответ'])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Выбрано
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Модель
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Ответ
        # Обработчик выделения ячейки (для активации кнопки при выделении колонки "Ответ")
        self.results_table.itemSelectionChanged.connect(self.on_result_selection_changed)
        self.results_table.cellClicked.connect(self.on_result_cell_clicked)
        self.results_table.setAlternatingRowColors(True)
        
        # Настройка многострочного отображения для колонки "Ответ"
        self.results_table.verticalHeader().setDefaultSectionSize(100)  # Минимальная высота строки
        self.results_table.setWordWrap(True)  # Включить перенос слов
        
        # Делегат для многострочного текста в колонке "Ответ"
        class MultiLineDelegate(QStyledItemDelegate):
            def sizeHint(self, option, index):
                size = super().sizeHint(option, index)
                if index.column() == 2:  # Колонка "Ответ"
                    text = index.data(Qt.DisplayRole) or ""
                    if text:
                        # Вычисляем высоту на основе количества строк
                        lines = text.split('\n')
                        line_count = len(lines)
                        # Минимум 3 строки, максимум 10 строк
                        height = max(60, min(300, line_count * 20 + 20))
                        size.setHeight(height)
                return size
        
        delegate = MultiLineDelegate(self.results_table)
        self.results_table.setItemDelegateForColumn(2, delegate)  # Колонка "Ответ"
        
        layout.addWidget(self.results_table)
        
        group.setLayout(layout)
        return group
    
    def create_buttons_area(self) -> QWidget:
        """Создание области кнопок"""
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Индикатор загрузки
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        self.send_btn = QPushButton('Отправить')
        self.send_btn.clicked.connect(self.send_requests)
        layout.addWidget(self.send_btn)
        
        self.open_btn = QPushButton('Открыть')
        self.open_btn.clicked.connect(self.open_selected_response)
        self.open_btn.setEnabled(False)
        layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton('Сохранить выбранные')
        self.save_btn.clicked.connect(self.save_selected_results)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton('Очистить')
        self.clear_btn.clicked.connect(self.clear_results)
        layout.addWidget(self.clear_btn)
        
        widget.setLayout(layout)
        return widget
    
    def load_prompts(self):
        """Загрузка списка промтов"""
        self.prompt_combo.clear()
        self.prompt_combo.addItem('-- Новый промт --', None)
        prompts = db.get_prompts()
        for prompt in prompts:
            text = f"{prompt['prompt'][:50]}..." if len(prompt['prompt']) > 50 else prompt['prompt']
            self.prompt_combo.addItem(text, prompt['id'])
    
    def load_models(self):
        """Загрузка списка моделей"""
        # Очистка существующих чекбоксов
        while self.models_layout.count():
            child = self.models_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Загрузка активных моделей
        active_models = models.get_active_models()
        self.model_checkboxes = {}
        
        for model in active_models:
            checkbox = QCheckBox(model.name)
            checkbox.setChecked(True)  # По умолчанию все выбраны
            self.model_checkboxes[model.id] = checkbox
            self.models_layout.addWidget(checkbox)
        
        self.models_layout.addStretch()
    
    def select_all_models(self):
        """Выбрать все модели"""
        for checkbox in self.model_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all_models(self):
        """Снять выбор со всех моделей"""
        for checkbox in self.model_checkboxes.values():
            checkbox.setChecked(False)
    
    def on_prompt_selected(self, index):
        """Обработчик выбора промта из списка"""
        prompt_id = self.prompt_combo.itemData(index)
        if prompt_id:
            try:
                prompt_data = db.get_prompt_by_id(prompt_id)
                if prompt_data:
                    self.prompt_input.setPlainText(prompt_data['prompt'])
                    self.current_prompt_id = prompt_id
                    # Очистка результатов при выборе нового промта
                    self.clear_results()
            except Exception as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить промт: {e}')
        else:
            # Выбран "Новый промт"
            self.current_prompt_id = None
            if not self.prompt_input.toPlainText().strip():
                self.clear_results()
    
    def get_selected_models(self) -> List[models.Model]:
        """Получить список выбранных моделей"""
        selected = []
        for model_id, checkbox in self.model_checkboxes.items():
            if checkbox.isChecked():
                model = models.get_model_by_id(model_id)
                if model:
                    selected.append(model)
        return selected
    
    def send_requests(self):
        """Отправка запросов к выбранным моделям"""
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, 'Предупреждение', 'Введите промт перед отправкой')
            return
        
        selected_models = self.get_selected_models()
        if not selected_models:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите хотя бы одну модель')
            return
        
        # Валидация моделей
        invalid_models = []
        for model in selected_models:
            is_valid, error_msg = model.validate()
            if not is_valid:
                invalid_models.append(f"{model.name}: {error_msg}")
        
        if invalid_models:
            error_text = 'Следующие модели имеют неверные настройки:\n\n' + '\n\n'.join(invalid_models) + \
                        '\n\nПроверьте настройки моделей в меню "Файл -> Управление моделями"'
            QMessageBox.warning(self, 'Ошибка валидации', error_text)
            return
        
        # Очистка предыдущих результатов
        self.clear_results()
        
        # Сохранение промта (если нужно)
        auto_save = db.get_setting('auto_save_prompts', 'false')
        if auto_save.lower() == 'true' and not self.current_prompt_id:
            try:
                self.current_prompt_id = db.create_prompt(prompt_text)
                self.load_prompts()
            except Exception as e:
                QMessageBox.warning(self, 'Предупреждение', f'Не удалось сохранить промт: {e}')
        
        # Если промт новый, создаем его
        if not self.current_prompt_id:
            try:
                self.current_prompt_id = db.create_prompt(prompt_text)
                self.load_prompts()
            except Exception as e:
                QMessageBox.warning(self, 'Предупреждение', f'Не удалось сохранить промт: {e}')
        
        # Настройка UI для загрузки
        self.send_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected_models))
        self.progress_bar.setValue(0)
        self.statusBar.showMessage(f'Отправка запросов к {len(selected_models)} моделям...')
        
        # Инициализация временной таблицы
        self.temp_results = []
        self.results_table.setRowCount(len(selected_models))
        
        # Добавление строк в таблицу
        for i, model in enumerate(selected_models):
            # Колонка 0: Выбрано (чекбокс)
            checkbox = QCheckBox()
            self.results_table.setCellWidget(i, 0, checkbox)
            # Колонка 1: Модель
            self.results_table.setItem(i, 1, QTableWidgetItem(model.name))
            # Колонка 2: Ответ
            self.results_table.setItem(i, 2, QTableWidgetItem('Загрузка...'))
            self.results_table.item(i, 2).setFlags(self.results_table.item(i, 2).flags() & ~Qt.ItemIsEditable)
        
        # Отправка запросов в отдельных потоках
        self.workers = []
        timeout = int(db.get_setting('default_timeout', '30'))
        
        for model in selected_models:
            worker = RequestWorker(model, prompt_text, timeout)
            worker.finished.connect(self.on_request_finished)
            self.workers.append(worker)
            worker.start()
    
    def on_request_finished(self, model_id: int, result: Dict):
        """Обработчик завершения запроса"""
        # Поиск строки с этой моделью
        for i in range(self.results_table.rowCount()):
            item = self.results_table.item(i, 1)  # Колонка "Модель"
            if item:
                model = models.get_model_by_id(model_id)
                if model and item.text() == model.name:
                    # Обновление ответа
                    response_text = result.get('response_text', 'Ошибка')
                    success = result.get('success', False)
                    
                    # Визуальное выделение ошибок
                    # Не обрезаем текст для многострочного отображения
                    response_item = QTableWidgetItem(response_text)
                    if not success:
                        response_item.setForeground(Qt.red)
                    
                    # Включаем перенос текста
                    response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    
                    # Устанавливаем максимальную длину только для tooltip
                    max_length = int(db.get_setting('max_response_length', '5000'))
                    if len(response_text) > max_length:
                        response_item.setToolTip(response_text)  # Полный текст при наведении
                    
                    self.results_table.setItem(i, 2, response_item)  # Колонка "Ответ"
                    self.results_table.item(i, 2).setFlags(
                        self.results_table.item(i, 2).flags() & ~Qt.ItemIsEditable)
                    
                    # Автоматическая настройка высоты строки
                    self.results_table.resizeRowToContents(i)
                    
                    # Сохранение во временную таблицу
                    self.temp_results.append({
                        'model_id': model_id,
                        'response_text': result.get('response_text', ''),
                        'metadata': result.get('metadata', {}),
                        'success': success
                    })
                    
                    # Обновление прогресса
                    current_value = self.progress_bar.value()
                    self.progress_bar.setValue(current_value + 1)
                    break
        
        # Проверка завершения всех запросов
        if self.progress_bar.value() >= self.progress_bar.maximum():
            self.send_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.save_btn.setEnabled(True)
            
            # Подсчет успешных и неуспешных запросов
            success_count = sum(1 for r in self.temp_results if r.get('success', False))
            total_count = len(self.temp_results)
            if success_count < total_count:
                self.statusBar.showMessage(
                    f'Запросы завершены: {success_count} успешно, {total_count - success_count} с ошибками')
            else:
                self.statusBar.showMessage('Все запросы успешно завершены')
    
    def save_selected_results(self):
        """Сохранение выбранных результатов в БД"""
        if not self.current_prompt_id:
            QMessageBox.warning(self, 'Предупреждение', 'Нет активного промта для сохранения')
            return
        
        saved_count = 0
        errors = []
        
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)  # Колонка "Выбрано"
            if checkbox and checkbox.isChecked():
                # Поиск соответствующего результата во временной таблице
                model_name = self.results_table.item(i, 1).text()  # Колонка "Модель"
                for temp_result in self.temp_results:
                    model = models.get_model_by_id(temp_result['model_id'])
                    if model and model.name == model_name:
                        try:
                            db.save_result(
                                self.current_prompt_id,
                                temp_result['model_id'],
                                temp_result['response_text'],
                                temp_result.get('metadata')
                            )
                            saved_count += 1
                        except Exception as e:
                            errors.append(f'{model_name}: {str(e)}')
                        break
        
        if saved_count > 0:
            message = f'Сохранено результатов: {saved_count}'
            if errors:
                message += f'\nОшибки:\n' + '\n'.join(errors)
            QMessageBox.information(self, 'Успех', message)
            self.clear_results()
        else:
            if errors:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить результаты:\n' + '\n'.join(errors))
            else:
                QMessageBox.warning(self, 'Предупреждение', 'Не выбрано ни одного результата для сохранения')
    
    def on_result_selection_changed(self):
        """Обработчик изменения выделения в таблице результатов"""
        self.update_open_button_state()
    
    def on_result_cell_clicked(self, row: int, column: int):
        """Обработчик клика по ячейке в таблице результатов"""
        self.update_open_button_state()
    
    def update_open_button_state(self):
        """Обновление состояния кнопки "Открыть" на основе выделения"""
        selected_items = self.results_table.selectedItems()
        if selected_items:
            # Проверяем, выделена ли колонка "Ответ" (колонка 2)
            for item in selected_items:
                if item.column() == 2:  # Колонка "Ответ"
                    # Проверяем, что в ячейке есть ответ (не "Загрузка...")
                    if item.text() and item.text() != 'Загрузка...':
                        self.open_btn.setEnabled(True)
                        return
            # Если выделена другая колонка, отключаем кнопку
            self.open_btn.setEnabled(False)
        else:
            self.open_btn.setEnabled(False)
    
    def open_selected_response(self):
        """Открыть диалог с форматированным ответом для выделенной ячейки в колонке "Ответ" """
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите ячейку с ответом в колонке "Ответ"')
            return
        
        # Ищем выделенную ячейку в колонке "Ответ" (колонка 2)
        row = None
        for item in selected_items:
            if item.column() == 2:  # Колонка "Ответ"
                row = item.row()
                break
        
        if row is None:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите ячейку в колонке "Ответ"')
            return
        
        self.open_response_dialog(row)
    
    def clear_results(self):
        """Очистка результатов"""
        # Остановка всех активных потоков
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.workers = []
        
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.save_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.send_btn.setEnabled(True)
        self.statusBar.showMessage('Результаты очищены')
    
    def show_prompts_window(self):
        """Показать окно управления промтами"""
        window = PromptsWindow(self)
        window.exec_()
        self.load_prompts()
    
    def show_models_window(self):
        """Показать окно управления моделями"""
        try:
            window = ModelsWindow(self)
            window.exec_()
            self.load_models()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть окно управления моделями:\n{e}')
            import traceback
            traceback.print_exc()
    
    def show_results_window(self):
        """Показать окно сохраненных результатов"""
        window = ResultsWindow(self)
        window.exec_()
    
    def open_response_dialog(self, row: int):
        """Открыть диалог с форматированным ответом в Markdown"""
        try:
            # Получение данных из таблицы
            model_name_item = self.results_table.item(row, 1)  # Колонка "Модель"
            response_item = self.results_table.item(row, 2)  # Колонка "Ответ"
            
            if not model_name_item or not response_item:
                return
            
            model_name = model_name_item.text()
            
            # Поиск полного текста ответа во временной таблице
            response_text = ""
            for temp_result in self.temp_results:
                model = models.get_model_by_id(temp_result['model_id'])
                if model and model.name == model_name:
                    response_text = temp_result.get('response_text', '')
                    break
            
            # Если не нашли во временной таблице, берем из ячейки
            if not response_text:
                response_text = response_item.text()
            
            # Создание и показ диалога с форматированным Markdown
            dialog = ResponseViewDialog(self, model_name, response_text)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть ответ:\n{e}')
            import traceback
            traceback.print_exc()
    
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(self, 'О программе', 
                         'ChatList v1.0\n\n'
                         'Приложение для сравнения ответов различных нейросетей\n'
                         'на один и тот же промт.')


class PromptsWindow(QDialog):
    """Окно управления промтами"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Управление промтами')
        self.setModal(True)
        self.resize(800, 600)
        self.all_prompts = []
        self.init_ui()
        self.load_prompts()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Введите текст для поиска...')
        self.search_input.textChanged.connect(self.filter_prompts)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Таблица промтов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['ID', 'Дата', 'Промт', 'Теги'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)  # Включение сортировки
        layout.addWidget(self.table)
        
        # Кнопки CRUD
        buttons_layout = QHBoxLayout()
        
        create_btn = QPushButton('Создать')
        create_btn.clicked.connect(self.create_prompt)
        buttons_layout.addWidget(create_btn)
        
        edit_btn = QPushButton('Изменить')
        edit_btn.clicked.connect(self.edit_prompt)
        buttons_layout.addWidget(edit_btn)
        
        view_btn = QPushButton('Просмотр')
        view_btn.clicked.connect(self.view_prompt)
        buttons_layout.addWidget(view_btn)
        
        buttons_layout.addStretch()
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_prompt)
        buttons_layout.addWidget(delete_btn)
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_prompts(self):
        self.all_prompts = db.get_prompts()
        self.filter_prompts()
    
    def filter_prompts(self):
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [p for p in self.all_prompts 
                       if search_text in p['prompt'].lower() or 
                          search_text in (p.get('tags', '') or '').lower()]
        else:
            filtered = self.all_prompts
        
        self.table.setRowCount(len(filtered))
        for i, prompt in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(prompt['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(prompt['date']))
            self.table.setItem(i, 2, QTableWidgetItem(prompt['prompt']))
            self.table.setItem(i, 3, QTableWidgetItem(prompt.get('tags', '')))
    
    def create_prompt(self):
        """Создание нового промта"""
        dialog = PromptDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_values()
            if prompt_text:
                try:
                    db.create_prompt(prompt_text, tags if tags else None)
                    self.load_prompts()
                    QMessageBox.information(self, 'Успех', 'Промт создан')
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось создать промт:\n{e}')
    
    def edit_prompt(self):
        """Редактирование выбранного промта"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите промт для редактирования')
            return
        
        prompt_id = int(self.table.item(row, 0).text())
        prompt_data = db.get_prompt_by_id(prompt_id)
        
        if not prompt_data:
            QMessageBox.warning(self, 'Ошибка', 'Промт не найден')
            return
        
        dialog = PromptDialog(self, prompt_data)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_values()
            if prompt_text:
                try:
                    db.update_prompt(prompt_id, prompt=prompt_text, tags=tags if tags else None)
                    self.load_prompts()
                    QMessageBox.information(self, 'Успех', 'Промт обновлен')
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить промт:\n{e}')
    
    def view_prompt(self):
        """Просмотр полного текста промта"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите промт для просмотра')
            return
        
        prompt_id = int(self.table.item(row, 0).text())
        prompt_data = db.get_prompt_by_id(prompt_id)
        
        if not prompt_data:
            QMessageBox.warning(self, 'Ошибка', 'Промт не найден')
            return
        
        # Создание диалога для просмотра
        view_dialog = QDialog(self)
        view_dialog.setWindowTitle(f'Просмотр промта #{prompt_id}')
        view_dialog.setModal(True)
        view_dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        view_dialog.setLayout(layout)
        
        # Информация о промте
        info_label = QLabel(f'<b>Дата:</b> {prompt_data["date"]}<br><b>Теги:</b> {prompt_data.get("tags", "")}')
        layout.addWidget(info_label)
        
        # Текст промта
        text_view = QTextEdit()
        text_view.setReadOnly(True)
        text_view.setPlainText(prompt_data['prompt'])
        layout.addWidget(text_view)
        
        # Кнопка закрытия
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(view_dialog.accept)
        layout.addWidget(buttons)
        
        view_dialog.exec_()
    
    def delete_prompt(self):
        """Удаление выбранного промта"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите промт для удаления')
            return
        
        prompt_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, 'Подтверждение', 
                                    f'Удалить промт #{prompt_id}?',
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                db.delete_prompt(prompt_id)
                self.load_prompts()
                QMessageBox.information(self, 'Успех', 'Промт удален')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить промт:\n{e}')


class ModelsWindow(QDialog):
    """Окно управления моделями"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Управление моделями')
        self.setModal(True)
        self.resize(900, 600)
        self.init_ui()
        self.load_models()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Таблица моделей
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Название', 'API URL', 'Ключ (env)', 'Тип', 'Активна'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_model)
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_model)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_model)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_models(self):
        try:
            models_list = models.get_all_models()
            self.table.setRowCount(len(models_list))
            for i, model in enumerate(models_list):
                self.table.setItem(i, 0, QTableWidgetItem(str(model.id)))
                self.table.setItem(i, 1, QTableWidgetItem(model.name))
                self.table.setItem(i, 2, QTableWidgetItem(model.api_url))
                self.table.setItem(i, 3, QTableWidgetItem(model.api_key_env))
                self.table.setItem(i, 4, QTableWidgetItem(model.model_type))
                
                checkbox = QCheckBox()
                checkbox.setChecked(model.is_active == 1)
                checkbox.stateChanged.connect(lambda state, m=model: 
                                             models.update_model(m.id, is_active=1 if state else 0))
                self.table.setCellWidget(i, 5, checkbox)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить модели:\n{e}')
            import traceback
            traceback.print_exc()
    
    def add_model(self):
        dialog = ModelDialog(self)
        if dialog.exec_():
            self.load_models()
    
    def edit_model(self):
        row = self.table.currentRow()
        if row >= 0:
            model_id = int(self.table.item(row, 0).text())
            model = models.get_model_by_id(model_id)
            if model:
                dialog = ModelDialog(self, model)
                if dialog.exec_():
                    self.load_models()
    
    def delete_model(self):
        row = self.table.currentRow()
        if row >= 0:
            model_id = int(self.table.item(row, 0).text())
            reply = QMessageBox.question(self, 'Подтверждение',
                                        f'Удалить модель #{model_id}?',
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                models.delete_model(model_id)
                self.load_models()


class ModelDialog(QDialog):
    """Диалог добавления/редактирования модели"""
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle('Редактировать модель' if model else 'Добавить модель')
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        if self.model:
            self.name_input.setText(self.model.name)
        form_layout.addRow('Название:', self.name_input)
        
        self.api_url_input = QLineEdit()
        if self.model:
            self.api_url_input.setText(self.model.api_url)
        form_layout.addRow('API URL:', self.api_url_input)
        
        self.api_key_env_input = QLineEdit()
        if self.model:
            self.api_key_env_input.setText(self.model.api_key_env)
        form_layout.addRow('Ключ (env):', self.api_key_env_input)
        
        self.model_type_input = QComboBox()
        self.model_type_input.addItems(['openai', 'deepseek', 'groq', 'anthropic', 'openrouter'])
        if self.model:
            index = self.model_type_input.findText(self.model.model_type)
            if index >= 0:
                self.model_type_input.setCurrentIndex(index)
        form_layout.addRow('Тип модели:', self.model_type_input)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        name = self.name_input.text().strip()
        api_url = self.api_url_input.text().strip()
        api_key_env = self.api_key_env_input.text().strip()
        model_type = self.model_type_input.currentText()
        
        if not all([name, api_url, api_key_env]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        try:
            if self.model:
                models.update_model(self.model.id, name=name, api_url=api_url,
                                   api_key_env=api_key_env, model_type=model_type)
            else:
                models.create_model(name, api_url, api_key_env, model_type)
            self.done(QDialog.Accepted)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить модель: {e}')
    
    def reject(self):
        self.done(QDialog.Rejected)


class ResultsWindow(QDialog):
    """Окно просмотра сохраненных результатов"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Сохраненные результаты')
        self.setModal(True)
        self.resize(1000, 600)
        self.all_results = []
        self.init_ui()
        self.load_results()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Введите текст для поиска...')
        self.search_input.textChanged.connect(self.filter_results)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'Промт', 'Модель', 'Ответ', 'Дата'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)  # Включение сортировки
        # Обработчик выделения для активации кнопки "Открыть"
        self.table.itemSelectionChanged.connect(self.on_result_selection_changed)
        self.table.cellClicked.connect(self.on_result_cell_clicked)
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.open_btn = QPushButton('Открыть')
        self.open_btn.clicked.connect(self.open_selected_response)
        self.open_btn.setEnabled(False)
        buttons_layout.addWidget(self.open_btn)
        
        export_md_btn = QPushButton('Экспорт Markdown')
        export_md_btn.clicked.connect(lambda: self.export_results('markdown'))
        buttons_layout.addWidget(export_md_btn)
        
        export_json_btn = QPushButton('Экспорт JSON')
        export_json_btn.clicked.connect(lambda: self.export_results('json'))
        buttons_layout.addWidget(export_json_btn)
        
        buttons_layout.addStretch()
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_result)
        buttons_layout.addWidget(delete_btn)
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_results(self):
        self.all_results = db.get_results()
        self.filter_results()
    
    def filter_results(self):
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [r for r in self.all_results 
                       if search_text in (r.get('prompt', '') or '').lower() or
                          search_text in (r.get('model_name', '') or '').lower() or
                          search_text in (r.get('response_text', '') or '').lower()]
        else:
            filtered = self.all_results
        
        self.table.setRowCount(len(filtered))
        for i, result in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(result['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(result.get('prompt', '')[:50]))
            self.table.setItem(i, 2, QTableWidgetItem(result.get('model_name', '')))
            response = result.get('response_text', '')
            max_len = 100
            if len(response) > max_len:
                response = response[:max_len] + '...'
            self.table.setItem(i, 3, QTableWidgetItem(response))
            self.table.setItem(i, 4, QTableWidgetItem(result.get('saved_date', '')))
    
    def export_results(self, format_type: str):
        """Экспорт результатов в Markdown или JSON"""
        from PyQt5.QtWidgets import QFileDialog
        import json
        from datetime import datetime
        
        if not self.all_results:
            QMessageBox.warning(self, 'Предупреждение', 'Нет результатов для экспорта')
            return
        
        if format_type == 'markdown':
            filename, _ = QFileDialog.getSaveFileName(
                self, 'Сохранить как Markdown', '', 'Markdown Files (*.md)')
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# Экспорт результатов ChatList\n\n")
                        f.write(f"Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"Всего результатов: {len(self.all_results)}\n\n")
                        f.write("---\n\n")
                        
                        for result in self.all_results:
                            f.write(f"## Результат #{result['id']}\n\n")
                            f.write(f"**Промт:** {result.get('prompt', '')}\n\n")
                            f.write(f"**Модель:** {result.get('model_name', '')}\n\n")
                            f.write(f"**Дата:** {result.get('saved_date', '')}\n\n")
                            f.write(f"**Ответ:**\n\n{result.get('response_text', '')}\n\n")
                            f.write("---\n\n")
                    
                    QMessageBox.information(self, 'Успех', f'Результаты экспортированы в {filename}')
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать: {e}')
        
        elif format_type == 'json':
            filename, _ = QFileDialog.getSaveFileName(
                self, 'Сохранить как JSON', '', 'JSON Files (*.json)')
            if filename:
                try:
                    export_data = {
                        'export_date': datetime.now().isoformat(),
                        'total_results': len(self.all_results),
                        'results': self.all_results
                    }
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                    
                    QMessageBox.information(self, 'Успех', f'Результаты экспортированы в {filename}')
                except Exception as e:
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать: {e}')
    
    def on_result_selection_changed(self):
        """Обработчик изменения выделения в таблице результатов"""
        self.update_open_button_state()
    
    def on_result_cell_clicked(self, row: int, column: int):
        """Обработчик клика по ячейке в таблице результатов"""
        self.update_open_button_state()
    
    def update_open_button_state(self):
        """Обновление состояния кнопки "Открыть" на основе выделения"""
        selected_items = self.table.selectedItems()
        if selected_items:
            # Проверяем, выделена ли колонка "Ответ" (колонка 3)
            for item in selected_items:
                if item.column() == 3:  # Колонка "Ответ"
                    if item.text() and item.text().strip():
                        self.open_btn.setEnabled(True)
                        return
            # Если выделена другая колонка, отключаем кнопку
            self.open_btn.setEnabled(False)
        else:
            self.open_btn.setEnabled(False)
    
    def open_selected_response(self):
        """Открыть диалог с форматированным ответом для выделенной ячейки в колонке "Ответ" """
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите ячейку с ответом в колонке "Ответ"')
            return
        
        # Ищем выделенную ячейку в колонке "Ответ" (колонка 3)
        row = None
        for item in selected_items:
            if item.column() == 3:  # Колонка "Ответ"
                row = item.row()
                break
        
        if row is None:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите ячейку в колонке "Ответ"')
            return
        
        self.open_response_dialog(row)
    
    def open_response_dialog(self, row: int):
        """Открыть диалог с форматированным ответом в Markdown"""
        try:
            # Получение данных из таблицы
            result_id_item = self.table.item(row, 0)  # Колонка "ID"
            model_name_item = self.table.item(row, 2)  # Колонка "Модель"
            response_item = self.table.item(row, 3)  # Колонка "Ответ"
            
            if not result_id_item or not model_name_item or not response_item:
                return
            
            model_name = model_name_item.text()
            
            # Получение полного текста ответа из БД
            result_id = int(result_id_item.text())
            result_data = db.get_result_by_id(result_id)
            
            if result_data:
                response_text = result_data.get('response_text', '')
            else:
                # Если не нашли в БД, берем из ячейки
                response_text = response_item.text()
            
            # Создание и показ диалога с форматированным Markdown
            dialog = ResponseViewDialog(self, model_name, response_text)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть ответ:\n{e}')
            import traceback
            traceback.print_exc()
    
    def delete_result(self):
        row = self.table.currentRow()
        if row >= 0:
            result_id = int(self.table.item(row, 0).text())
            reply = QMessageBox.question(self, 'Подтверждение',
                                        f'Удалить результат #{result_id}?',
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                db.delete_result(result_id)
                self.load_results()


class PromptDialog(QDialog):
    """Диалог для создания/редактирования промта"""
    def __init__(self, parent=None, prompt_data=None):
        super().__init__(parent)
        self.prompt_data = prompt_data
        self.setWindowTitle('Редактировать промт' if prompt_data else 'Создать промт')
        self.setModal(True)
        self.resize(600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Поле для текста промта
        self.prompt_input = QTextEdit()
        if self.prompt_data:
            self.prompt_input.setPlainText(self.prompt_data.get('prompt', ''))
        self.prompt_input.setPlaceholderText('Введите текст промта...')
        form_layout.addRow('Промт:', self.prompt_input)
        
        # Поле для тегов
        self.tags_input = QLineEdit()
        if self.prompt_data:
            self.tags_input.setText(self.prompt_data.get('tags', ''))
        self.tags_input.setPlaceholderText('Теги через запятую (необязательно)')
        form_layout.addRow('Теги:', self.tags_input)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        """Получить значения из формы"""
        prompt_text = self.prompt_input.toPlainText().strip()
        tags_text = self.tags_input.text().strip()
        return prompt_text, tags_text if tags_text else None
    
    def accept(self):
        """Проверка перед принятием"""
        prompt_text, _ = self.get_values()
        if not prompt_text:
            QMessageBox.warning(self, 'Ошибка', 'Введите текст промта')
            return
        super().accept()


class ResponseViewDialog(QDialog):
    """Диалог для просмотра ответа в форматированном Markdown"""
    def __init__(self, parent=None, model_name: str = "", response_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle(f'Ответ: {model_name}')
        self.setModal(True)
        self.resize(800, 600)
        self.init_ui(model_name, response_text)
    
    def init_ui(self, model_name: str, response_text: str):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок с названием модели
        header_label = QLabel(f'<h2>Ответ модели: {model_name}</h2>')
        layout.addWidget(header_label)
        
        # Текстовое поле для отображения Markdown
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Сохранение оригинального текста для копирования
        self.original_text = response_text
        
        # Попытка использовать setMarkdown (доступно в Qt 5.14+)
        try:
            # Проверяем наличие метода setMarkdown
            if hasattr(self.text_view, 'setMarkdown'):
                self.text_view.setMarkdown(response_text)
            else:
                # Если setMarkdown недоступен, конвертируем markdown в HTML
                self.text_view.setHtml(self.markdown_to_html(response_text))
        except Exception as e:
            # В случае ошибки используем обычный текст
            self.text_view.setPlainText(response_text)
        
        layout.addWidget(self.text_view)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        copy_btn = QPushButton('Копировать')
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.original_text))
        buttons_layout.addWidget(copy_btn)
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def markdown_to_html(self, markdown_text: str) -> str:
        """Простая конвертация Markdown в HTML (базовая поддержка)"""
        html = markdown_text
        
        # Заголовки
        import re
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Жирный текст
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
        
        # Курсив
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
        
        # Код (inline)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Блоки кода
        html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        
        # Списки
        lines = html.split('\n')
        in_list = False
        result_lines = []
        for line in lines:
            if re.match(r'^[-*+] ', line):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line[2:]}</li>')
            elif re.match(r'^\d+\. ', line):
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = True
                result_lines.append(f'<li>{re.sub(r"^\d+\. ", "", line)}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>' if '<ol>' not in '\n'.join(result_lines[-10:]) else '</ol>')
                    in_list = False
                if line.strip():
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append('<br>')
        
        if in_list:
            result_lines.append('</ul>')
        
        html = '\n'.join(result_lines)
        
        # Заменяем переносы строк на <br>
        html = html.replace('\n', '<br>')
        
        return f'<div style="font-family: Arial, sans-serif; padding: 10px;">{html}</div>'
    
    def copy_to_clipboard(self, text: str):
        """Копировать текст в буфер обмена"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, 'Успех', 'Текст скопирован в буфер обмена')


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
