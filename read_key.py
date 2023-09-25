'''
Зчитує поточний комплект ключів (e, d, n) з файла key.txt, формат файла - csv, роздільник - ';'
Зміна ключів - шляхом циклічного зсуву даних індексного файла index.key.txt при кожному зверненні
'''
import os

def get_index_key():
    '''
    виконує циклічний зсув вліво даних індексного файла, що визначає позиції рядків з ключами
    у файлі key.txt
    Вертає останній елемент списка позицій (перший до зсуву)
    Якщо індексний файл не існує, то створює індексний список функцією index_file()
    '''
    if not 'index_key.txt' in os.listdir():
        index_key = [str(el) for el in index_file('key.txt')]
    else:
        with open('index_key.txt', 'r') as file:
            index_key = file.readline().split()
    index_key.append(index_key.pop(0)) # циклічний зсув списка index_key вліво
    with open('index_key.txt', 'w') as file:
          file.write(' '.join(index_key))
    return int(index_key[-1])

def index_file(file):
    '''
    Cтворює індексний список з переданого файла (елементи списка - початкові позиції рядків)
    шляхом зчитування його рядками,
    починає список з позиції 0, при поверненні індексного списка відкидає останній елемент,
    як позицію кінця файла
    '''
    lines_index = [0]
    with open(file, 'r') as in_file:
        while in_file.readline():
            lines_index.append(in_file.tell())
    return lines_index[:-1]

def get_key():
    '''
    Вертає поточні ключі (значення e, d, n) з файла набору ключів key.txt
    Позиція рядка, який буде зчитуватись визначається функцією get_index_key()
    '''
    with open('key.txt', 'r') as in_file:
        in_file.seek(get_index_key())
        e, d, n = in_file.readline().rstrip().split(';')
    return e, d, n    
    
if __name__ == '__main__':
    e, d, n = get_key()
    print('e =', e)
    print('d =', d)
    print('n =', n)

