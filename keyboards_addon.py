# Дополнительные клавиатуры для расширенных функций библиотеки
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def library_kb_extended():
    '''Расширенная клавиатура для библиотеки с фильтрами'''
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🎨 Созданные', callback_data='lib_show_generated'),
         InlineKeyboardButton('📤 Загруженные', callback_data='lib_show_uploaded')],
        [InlineKeyboardButton('✏️ Отредактированные', callback_data='lib_show_edited'),
         InlineKeyboardButton('⭐ Избранное', callback_data='lib_show_favorites')],
        [InlineKeyboardButton('📁 Все', callback_data='lib_show_all')],
        [InlineKeyboardButton('🔍 Фильтры', callback_data='lib_filters'),
         InlineKeyboardButton('📊 Статистика', callback_data='lib_stats')],
        [InlineKeyboardButton('📦 Экспорт', callback_data='lib_export'),
         InlineKeyboardButton('🏷️ Теги', callback_data='lib_tags')]
    ])


def library_filters_kb():
    '''Клавиатура фильтров по дате'''
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📅 За сегодня', callback_data='lib_filter_1'),
         InlineKeyboardButton('📅 За неделю', callback_data='lib_filter_7')],
        [InlineKeyboardButton('📅 За месяц', callback_data='lib_filter_30'),
         InlineKeyboardButton('📅 Все время', callback_data='lib_filter_all')],
        [InlineKeyboardButton('◀️ Назад', callback_data='lib_back')]
    ])


def image_actions_kb(blob_name, in_favorites=False):
    '''Клавиатура действий с изображением'''
    fav_text = '💔 Убрать из избранного' if in_favorites else '⭐ В избранное'
    fav_data = f'img_unfav_{blob_name}' if in_favorites else f'img_fav_{blob_name}'
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(fav_text, callback_data=fav_data)],
        [InlineKeyboardButton('🔗 Поделиться', callback_data=f'img_share_{blob_name}'),
         InlineKeyboardButton('🗑️ Удалить', callback_data=f'img_delete_{blob_name}')],
        [InlineKeyboardButton('🏷️ Добавить теги', callback_data=f'img_tags_{blob_name}')],
        [InlineKeyboardButton('◀️ Назад к списку', callback_data='lib_back')]
    ])


def pagination_kb(current_page, total_pages, category):
    '''Клавиатура пагинации'''
    buttons = []
    
    # Кнопки навигации
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton('◀️ Назад', callback_data=f'lib_page_{category}_{current_page-1}'))
    
    nav_row.append(InlineKeyboardButton(f'{current_page+1}/{total_pages}', callback_data='lib_page_info'))
    
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton('Вперед ▶️', callback_data=f'lib_page_{category}_{current_page+1}'))
    
    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton('◀️ К категориям', callback_data='lib_back')])
    
    return InlineKeyboardMarkup(buttons)


def export_options_kb():
    '''Клавиатура опций экспорта'''
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📦 Все изображения', callback_data='export_all')],
        [InlineKeyboardButton('🎨 Только созданные', callback_data='export_generated'),
         InlineKeyboardButton('✏️ Только отредактированные', callback_data='export_edited')],
        [InlineKeyboardButton('⭐ Только избранное', callback_data='export_favorites')],
        [InlineKeyboardButton('◀️ Назад', callback_data='lib_back')]
    ])


def confirm_delete_kb(blob_name):
    '''Подтверждение удаления изображения'''
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Да, удалить', callback_data=f'img_delete_confirm_{blob_name}')],
        [InlineKeyboardButton('❌ Отмена', callback_data='lib_back')]
    ])
