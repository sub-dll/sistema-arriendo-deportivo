from database import init_db
from ui import ArriendoApp


def main():
    init_db()
    app = ArriendoApp()
    app.mainloop()


if __name__ == "__main__":
    main()