# Ansible

Сейчас в Ansible написаны 3 роли:
1. setup-worker-servers
2. stub-sites
3. xray-server

#### setup-worker-servers

Базовая настройка сервера для безопасности, то есть создание нового пользователя, изменения поролей, изменения порта для ssh (выбирается рандомно, есть защита от изменения на занятый порт), создания виртуального окружения Python. Все новые данные о сервере сохраняются в json файл только на master сервере (delegate_to: localhost)

#### stub-sites

Копирует nginx.conf, html страницу, запускает сайт, язык сайта зависит от ip сервера (geoip)

#### xray-server

Устанавливает xray на сервере, копирует xray.service, xray.conf. Все версии конфигурации xray хранятся в репозитории, Ansible берет последнюю (ссылается через символическую ссылку), запускает xray с указанием пути на все файлы настройки xray. Так же копирует все необходимые скрипты для работы с этими настройками (добавление пользователей, удаление пользователей, необходимый для gRPC код)

#### Inventory 

Инвентарь создается динамически, данные беруться из postgreSQL, хосты не меняются местами от запуска к запуску. Для добавления новых серверов написан скрипт, который подгружает их в базу данных. Информация для подключения к базе данных хранится в ansible vault в зашифрованном виде, уже начал разбираться с HashiCorp Vault, надо переходить на него


# gRPC 

Решил писать общение между master сервером и worker серверами на gRPC. Пока разбираюсь с подключением сертификатов, но уже работает так.

# HashiCorp Vault

Написал конфиг для Vault, создал политику, добавил хранилище k/v, создал пользователя. Все работает через API с self-signed сертификатом.