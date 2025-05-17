#list of all Tekken 8 fighters for tesseract to read and match to
fighter_list = [
        'KAZUYA',
        'JIN',
        'KING',
        'JUN',
        'PAUL',
        'LAW',
        'JACK', #JACK-8 is hard for tesseract to read
        'LARS',
        'XIAOYU',
        'NINA',
        'LEROY',
        'ASUKA',
        'LILI',
        'BRYAN',
        'HWOARANG',
        'CLAUDIO',
        'AZUCENA',
        'RAVEN',
        'LEO',
        'STEVE',
        'KUMA',
        'YOSHIMITSU',
        'SHAHEEN',
        'DRAGUNOV',
        'FENG',
        'PANDA',
        'LEE',
        'ALISA',
        'ZAFINA',
        'DEVILJIN', #spaces are removed in tesseract post-processing
        'VICTOR',
        'REINA'
    ]

#for logging and print statements
class asciiColor:
    """
    asciiColor

    ANSI escape codes to style terminal text with colors, backgrounds, and text styles.

    Attributes:
        reset (str): Resets all terminal text formatting to default.

    Classes:
        bg:
            Contains ANSI escape codes for background colors.

            Subclass:
                bright:
                    Contains ANSI escape codes for bright background colors.
                    
        fg:
            Contains ANSI escape codes for foreground (text) colors.

            Subclass:
                bright:
                    Contains ANSI escape codes for bright foreground (text) colors.

        style:
            Contains ANSI escape codes for text styles.
    """
    reset = '\033[0m'

    #background
    class bg:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        YELLOW = '\033[43m'
        BLUE = '\033[44m'
        MAGENTA = '\033[45m'
        CYAN = '\033[46m'
        WHITE = '\033[47m'

        class bright:
            BLACK = '\033[100m'
            RED = '\033[101m'
            GREEN = '\033[102m'
            YELLOW = '\033[103m'
            BLUE = '\033[104m'
            MAGENTA = '\033[105m'
            CYAN = '\033[106m'
            WHITE = '\033[107m'

    #foreground
    class fg:
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'

        class bright:
            BLACK = '\033[90m'
            RED = '\033[91m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            BLUE = '\033[94m'
            MAGENTA = '\033[95m'
            CYAN = '\033[96m'
            WHITE = '\033[97m'

    class style:
        bold = '\033[1m'
        italic = '\033[3m'
        underline = '\033[4m'
        strike = '\033[9m'
        
#headers for web/youtube requests
request_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "identity",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}