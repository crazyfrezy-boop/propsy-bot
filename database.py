import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        # ТЕСТОВЫЙ РЕЖИМ - данные в памяти
        self.test_mode = True
        self.test_users = {}
        self.test_tasks = {}
        print("⚠️ ТЕСТОВЫЙ РЕЖИМ: данные не сохраняются в Airtable")
        print("✅ База данных готова (тестовая)")
    
    def get_user(self, user_id):
        """Получить пользователя по ID"""
        if user_id is None:
            return None
        return self.test_users.get(str(user_id))
    
    def create_user(self, user_id, name, role, psychologist_id=None):
        """Создать нового пользователя"""
        print(f"🔍 create_user: user_id={user_id}, name={name}, role={role}")
        
        # Генерируем ID если его нет
        if user_id is None:
            user_id = int(datetime.now().timestamp())
        
        user_data = {
            'user_id': str(user_id),
            'name': name,
            'role': role,
            'phone': '',
            'psychologist_id': str(psychologist_id) if psychologist_id else '',
            'sessions': 0,
        }
        
        if role == 'psychologist':
            user_data['trial_until'] = (datetime.now() + timedelta(days=14)).isoformat()
        
        self.test_users[str(user_id)] = user_data
        print(f"✅ Пользователь {name} создан (всего пользователей: {len(self.test_users)})")
        return user_id
    
    def update_user_phone(self, user_id, phone):
        """Обновить телефон пользователя"""
        if str(user_id) in self.test_users:
            self.test_users[str(user_id)]['phone'] = phone
            print(f"✅ Телефон обновлён для {user_id}")
    
    def get_psychologists(self):
        """Получить всех психологов"""
        result = []
        for u in self.test_users.values():
            if u.get('role') == 'psychologist':
                result.append(u)
        print(f"🔍 Найдено психологов: {len(result)}")
        return result
    
    def get_psychologist_clients(self, psychologist_id):
        """Получить клиентов психолога"""
        result = []
        for u in self.test_users.values():
            if u.get('psychologist_id') == str(psychologist_id) and u.get('role') == 'client':
                result.append(u)
        print(f"🔍 Найдено клиентов у психолога {psychologist_id}: {len(result)}")
        return result
    
    def add_task(self, client_id, text, psychologist_id):
        """Добавить домашнее задание"""
        task_id = int(datetime.now().timestamp())
        task = {
            'id': task_id,
            'client_id': str(client_id),
            'psychologist_id': str(psychologist_id),
            'text': text,
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        self.test_tasks[task_id] = task
        print(f"📝 Добавлено задание {task_id} для клиента {client_id}")
        return task_id
    
    def get_client_tasks(self, client_id, only_active=False):
        """Получить задания клиента"""
        result = []
        for task in self.test_tasks.values():
            if task.get('client_id') == str(client_id):
                if only_active and task.get('completed'):
                    continue
                result.append(task)
        return result
    
    def check_subscription(self, user_id):
        """Проверить подписку (в тестовом режиме всегда активна)"""
        return True
    
    def activate_payment(self, user_id):
        """Активировать платную подписку"""
        print(f"💰 Активация подписки для {user_id}")
        pass
    
    def save_mood(self, user_id, mood):
        """Сохранить настроение"""
        print(f"📊 Сохранение настроения: user={user_id}, mood={mood}")
        pass
    
    def create_appointment(self, client_id, psychologist_id, datetime_obj):
        """Создать запись на сессию"""
        print(f"📅 Запись на сессию: client={client_id}, psy={psychologist_id}")
        return 1
    
    def get_upcoming_appointments(self, hours=None, minutes=None):
        """Получить предстоящие записи"""
        return []
    
    def add_mood_comment(self, user_id, mood, comment):
        pass
    
    def get_mood_history(self, user_id, days=7):
        return []
    
    def complete_task(self, task_id):
        pass