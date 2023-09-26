A simple HTTP server based monitoring and control system on ESP32 MicroPython

V0.16, 07.09.2023

Author: Oleksandr Teteria

Requires: ESP32 Board. Any firmware version dated 2020 or later. For temperature, humidity, pressure monitoring - sensor modules BMP280, DHT22. To control external devices - a relay module.

# Contents

1. [Overview](./README.md#1-overview)
2. [Design](./README.md#2-design)
3. [Install](./README.md#3-install)
4. [Monitoring and control capabilities](./README.md#4-monitoring-and-control-capabilities)
5. [Implementation stages and some explanations](./README.md#5-implementation-stages-and-some-explanations)

# 1. Overview

The web server is implemented based on ESP32 MicroPython. The BMP280 sensor module was used for pressure monitoring. A DHT22 sensor module is used to monitor temperature and humidity. To display information, a WS2812 matrix is ​​used, which is controlled by a Raspberry Pi Pico microcontroller. The MicroPython web server, using the ESP32 microcontroller board, allows you to control the relay module. Communication between raspberry pi pico and ESP32 controllers via the UART interface.

A general view of the user interface served by our web server is presented at [HTTP-ESP32-Server](https://alex-teteria.github.io/MicroPython-HTTP-Server-Templates/). The web server serves this HTML page with values ​​or template variables that need to be resolved based on sensor values ​​and commands or data from the client.

Login to the user page is carried out by entering a password. The SHA-256 hashing algorithm is used to protect the password during transmission. The digest is the result of the hash function of the entered password + the initialization vector (a random string received from the server).

The RSA cryptoalgorithm is used to send a new password when the user changes it.

Web server configuration is done through an HTML page.

# 2. Design

Below is a diagram of the entire system, which consists of a web server on an ESP32, a display controller for a WS2812 matrix on a Raspberry Pi Pico, sensor modules and a relay module.

![Web_Server_ESP32](https://github.com/Alex-Teteria/ESP32_WebServer/assets/94607514/2a11045d-92b0-40e1-8e23-d1bf7e7ca4c1)

This is what a system prototype can look like, which is implemented on development boards for ESP32 and Raspberry PI Pico :)

![prototype_ESP32_server](https://github.com/Alex-Teteria/ESP32_WebServer/assets/94607514/7966f2d1-a547-478b-a552-6a9daa4e816f)

# 3. Install

Upload all of these to your project folder. When downloading, you should keep the same placement of files in folders. Use [Thonny IDE](https://thonny.org/) or other IDE for upload your code in ESP32 board.

| File | Purpose |
| --- | --- |
| main.py | The main code is saved as main.py, so the code is executed every time the ESP32 is started. |
| bmp280.py | A library  [bmp280](https://github.com/dafvid/micropython-bmp280) that has functions to work with the BMP280 sensor. |
| read_key.py | Module for working with keys. |
| config.txt | A text file with the current network settings. |
| config_devices.txt | A text file containing information about the initial state of the relay. |
| key.txt | A set of pre-generated 512-bit RSA keys. Given as an example, when the server is functioning, they must be replaced with their own set ! |
| passwd.txt | Current server login password. |
| /html | Folder containing templates, style files, image files. |

###### [Top](./README.md#contents)

# 4. Monitoring and control capabilities

- Obtaining temperature and humidity values ​​using the DHT22 module.
- Obtaining the pressure value using the BMP280 module.
- Control of external devices through the relay module.
- Sending sensor readings for display on a WS2812 type LED display

Sending data for display on a WS2812 type LED display:

- sensor readings;
- some text;
- current time.

- Ability to choose Wi-Fi connection mode - Station mode or Access point mode with appropriate network settings.
- It is possible to set the initial state of the relay.
- Login to the server using a password that is protected when forwarding by the SHA-256 hashing algorithm.
- It is possible to change the login password. The RSA crypto-algorithm was used to send the new password.

###### [Top](./README.md#contents)

# 5. Implementation stages and some explanations

v.3 18.07.2023

Тестова реалізація пересилання інформації (в UTF-8), наприклад паролю, за допомогою криптоалгоритму RSA. При цьому використовується попередньо згенерований комплект ключів (256-біт ):
e - відкритий ключ, d - закритий ключ, n - модуль.
Відкритий ключ та модуль відсилаються клієнту на GET запит path='/main_menu' або path='/' як змінні e та n javascript у файлі main_menu_3.html.
На стороні клієнта (web browser) функція changeNumber() викликається по події onsubmit, використовує дані, які введені в полі форми text, з ідентифікатором "myInput" (input = document.getElementById("myInput")), змінює їх на шифр (у вигляді числа) та вертає в поле вводу даних. При цьому введені дані спочатку перетворюються на байтовий масив (uint8Array), потім цей байтовий масив перетворюється на ціле число типу BigInt функцією byteArrayToLong(byteArray) за алгоритмом:
якщо байтовий масив [..., b3, b2, b1, b0], то ціле число буде:
b0 + b1*256 + b2*256**2 + b3*256**3 + ...
аналог - метод цілих чисел Python int.from_bytes(bytes, byteorder='big', *, signed=False), якщо byteorder='little', то міняється порядок слідування коефіцієнтів при розрахунку, тобто b0 буде старшим розрядом.
Далі, використовуючи швидкий рекурсивний алгоритм обчислення степеня числа по модулю, функція recursePowToMod(m, e, n), обчислюється зашифроване повідомлення, як m ** e (mod n), де m - відкрите повідомлення, в нашому випадку змінна in_num = byteArrayToLong(uint8Array) * 100n + lenArray,
число що відповідає байтовому масиву відкритого повідомлення, до якого добавили довжину цього масива.
Добавлення довжини масива - це спосіб передачі цієї довжини серверу. Вона необхідна для обчислення байтів інформації з отриманого числа за допомогою функції int.to_bytes(length, byteorder='big', *, signed=False), length - очікувана кількість байтів.

v.5
Добавлено меню Login, яке активізується при виході (пункт меню Exit)
Реалізація:
Глобальна змінна flag_login приймає значення True, коли прийнятий пароль співпадає
із зчитаним з файла "passwd.txt", при цьому на POST запит передається 'html/menu.html'(сторінка основного меню)
В основному циклі, коли flag_login == True - перехід на обробку усіх запитів,
а коли False, перехід на обробку відсилання сторінки "Login" (функція send_login).
Для захисту пересилання паролю використано алгоритм хешування SHA-256.
При цьому дайджест отримуємо як результат хеш-функції введеного пароля + вектора ініціалізації, рядка з 8 байтів, які генеруються випадково функцією random_string та передаються як константа "init_vector" сторінкою login.html при кожному новому запиті із path == /login.html.
Вектор ініціалізації, глобальна змінна random_str, генерується при першому запиті GET, а при запиті POST відбувається читання з файла "passwd.txt" пароля, додавання до нього random_str та формування дайджеста: result = hashlib.sha256(passwd + random_str). Результат порівнюється з отриманим із запита POST: if passwd_hash == d_body['passwd']:...

v.6 27.07.2023
Добавлено модуль read_key. Реалізовано зчитування поточних ключів (e, d, n) з файла key.txt. Зміна ключів при кожному звертанні забезпечується циклічним зсувом даних індексного файла index_key.txt, який визначає положення рядків у файлі key.txt
Відповідно внесено зміни у функцію send_settings().

v.7 28.07.2023
Добавлено обслуговування сенсера АМ2301 (DHT22), відповідно внесено зміни у файл sens_status.html та функцію send_sens_status().
Використано бібліотечний модуль dht для роботи з сенсером.

v.8 29.07.2023
Добавлено обслуговування сенсера вимірювача тиску bmp280, відповідно внесено зміни у файл sens_status.html та функцію send_sens_status(). Використано модуль bmp280 для роботи з сенсером. Уникнено зависань у випадках, коли сокет відкритий (client connected from (....)) та довго чекає даних із сокета: line = cl_file.readline() # тут можливе зависання. Тому встановлено тайм-аут блокування сокета (socket.settimeout(5.0)) на 5 секунд. При цьому операції з сокетом розміщено в try: ..., по спрацюванню тайм-аута виникає помилка OSError, для виключення якої сокет закривається - except OSError: cl.close().

v.9 02.08.2023
Добавлено зв'язок з raspberry pi pico по інтерфейсу uart:
uart = machine.UART(2,9600)
При отриманні запиту з відправленим текстом, метод POST,
відсилаємо отриманий текст по лінії Tx2 до Pi Pico: uart.write(d_body['text'])

v.10
Добавлено меню Send Time. На контролер Led посилається значення діючого часу, яке отримано при запиті з Path '/send_time.html'
В menu.html добавлено тег <button type="button" onclick="url()">Send Time</button>
та js з функцією url(), яка виконується при активації цього button:
function url(){
 let now = new Date();
 window.open('send_time.html?'+now.getHours()+':'+now.getMinutes(), '_self')
 }
Функція формує запит з Path "send_time.html" та параметром "год:хв"
У функцію send_main_menu добавлено обробку запита з path == "send_time.html", а саме
як параметр береться значення год:хв та відсилається на контролер Led по UART:
uart.write('AT&time;' + params + '\r\n')

v.13
Добавлена можливість налаштування веб-сервера із HTML-сторінки.
Добавлені відповідні пункти меню та сторінка config_connection.html.
Є можливість вибрати режим роботи Wi-Fi: Access point mode або Station mode
При цьому створюємо примірник об'єкта мережі інтерфейса WLAN: wlan = create_wlan()
В залежності від параметру 'ap_mode', який заданий в файлі конфігурації, функція create_wlan() створює примірник wlan, як точку доступу (access point), або клієнта (station mode).При цьому викликаються відповідно функції create_accesspoint() або connect().
Решта конфігураційних параметрів також записано у файл config.txt
Реалізовано завантаження сервера з параметрами за замовчуванням:
включення живлення при натиснутій кнопці "button_reset" (GPIO_13 == 0)
при цьому режим буде access point з налаштуванням:
ssid = ESP-32
password = 12345678
ip = 192.168.8.2, mask = 255.255.255.0, gw = 192.168.8.1, dns = 8.8.8.8
Крім того, це саме значення password ('12345678') записується у файл passwd.txt,
як пароль доступу до вебсервера

v.14 25.08.2023
Добавлено зчитування конфігурації з файла config.txt
при запиті з path = '/config_connection.html' (функція config_connection)
При цьому добавлено посилання на значення відповідних параметрів у html-файл config_connection.html (value="%s")
Зчитані з конфігураційного файла параметри добавляються у config_connection.html при його відсиланні

v.15
Змінено пункт меню "Devices Management" у menu.html: замість sens_manager.html - dev_manager.html. Відповідно змінено словник функцій обробки запитів d_send, добавлено 'dev_manager.html': dev_manager.
Добавлено функцію обробки цього запиту dev_manager
добавлено примірники об'єкту machine.Pin - relay_1, relay_2 - виходи на управління реле. Об'єднано обробку усіх запитів на відправку файлів зображень в
одну функцію send_image.

v.16 07.09.2023
Добавлено пункт меню "Devices" в сторінці config_main.html для встановлення початкового стану реле (relay_1, relay_2) при включенні живлення
Для цього додатково створено сторінку config_devices.html та файл де записано початковий стан реле - config_devices.txt
config_devices - функція обробки запиту
init_devices - функція зчитує файл config_devices.txt та встановлює виходи відповідно до значень relay1, relay2 ('On' або 'Off')
###### [Top](./README.md#contents)
