import shelve
from config import shelve_status

# Set to storage with name
def set_storage(name, id, mes):
    with shelve.open(name) as stor:
        stor[str(id)] = mes
        
# Получаем данные из хранилища name
def get_storage(name, id):
    with shelve.open(name) as storage:
        try:
            answer = storage[str(id)]
            return answer
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None

# Удаляем данные из хранилища
def del_storage(name, id):
    with shelve.open(name) as storage:
        if (str(id) in storage):
            del storage[str(id)]