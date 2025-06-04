import wx
import wx.grid as gridlib
import psycopg2

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Построитель таблиц", size=(1200, 700))
        self.InitUI()
        self.Show()

    def InitUI(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Панель фильтров для таблицы full_income
        income_filter_box = wx.StaticBox(panel, label="Фильтр для таблицы доходов")
        income_filter_sizer = wx.StaticBoxSizer(income_filter_box, wx.VERTICAL)

        # Регион
        self.income_region_choices = self.create_choice(panel, "Регион", income_filter_sizer, self.get_regions())
        # Год
        self.income_year_choices = self.create_choice(panel, "Год", income_filter_sizer, self.get_years())
        # Возраст
        self.income_age_choices = self.create_choice(panel, "Возраст", income_filter_sizer, self.get_ages())
        # Пол
        self.income_gender_choices = self.create_choice(panel, "Пол", income_filter_sizer, ["male", "female", "all","Все значения"])
        # Family income
        self.family_income_choices = self.create_choice(panel, "Доход семьи", income_filter_sizer, self.get_family_incomes())
        # Age_of_older
        self.age_of_older_choices = self.create_choice(panel, "Возраст старшего", income_filter_sizer, ["0 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 54 years", "55 to 64 years", "Total all ages","Все значения"])

        # Панель фильтров для таблицы full_expense
        expense_filter_box = wx.StaticBox(panel, label="Фильтр для таблицы расходов")
        expense_filter_sizer = wx.StaticBoxSizer(expense_filter_box, wx.VERTICAL)

        # Регион
        self.expense_region_choices = self.create_choice(panel, "Регион", expense_filter_sizer, self.get_regions())
        # Год
        self.expense_year_choices = self.create_choice(panel, "Год", expense_filter_sizer, self.get_years())
        # Возраст
        self.expense_age_choices = self.create_choice(panel, "Возраст", expense_filter_sizer, self.get_ages())
        # Пол
        self.expense_gender_choices = self.create_choice(panel, "Пол", expense_filter_sizer, ["male", "female", "all" ,"Все значения"])
        # Категория
        self.category_choices = self.create_choice(panel, "Категория", expense_filter_sizer, self.get_categories())
        # Квинтиль
        self.quintile_choices = self.create_choice(panel, "Квинтиль", expense_filter_sizer, self.get_quintiles())

        # Кнопки для построения таблиц
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_build_income = wx.Button(panel, label="Построить таблицу доходов")
        self.btn_build_expense = wx.Button(panel, label="Построить таблицу расходов")
        btn_sizer.Add(self.btn_build_income, flag=wx.RIGHT, border=10)
        btn_sizer.Add(self.btn_build_expense, flag=wx.RIGHT, border=10)

        self.btn_build_income.Bind(wx.EVT_BUTTON, self.on_build_income)
        self.btn_build_expense.Bind(wx.EVT_BUTTON, self.on_build_expense)

        # Таблица для отображения данных
        self.grid = gridlib.Grid(panel)
        self.grid.CreateGrid(0, 0)

        # Собираем все
        main_sizer.Add(income_filter_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(expense_filter_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(btn_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(self.grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        panel.SetSizer(main_sizer)

    def create_choice(self, parent, label, sizer, choices):
        box = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(parent, label=label)
        choice = wx.Choice(parent, choices=choices)
        choice.SetSelection(0)
        box.Add(lbl, flag=wx.RIGHT, border=5)
        box.Add(choice)
        sizer.Add(box, flag=wx.EXPAND | wx.ALL, border=5)
        return choice

    def get_regions(self):
        #region1 = [str(x) for x in range(1, 14) ]
        #return region1
        # Получить регионы из базы
        return self.query_single_column("SELECT region FROM region ORDER BY region_id")+["Все значения"]

    def get_years(self):
        # Получить года (2010-2021, исключая 2018 и 2020)
        years = [str(y) for y in range(2010, 2022) if y not in (2018, 2020)]+["Все значения"]
        return years

    def get_ages(self):
        return ["0-34","35-64", "all ages"]+["Все значения"]
        #return ["0 to 24 ages", "25 to 34 ages", "35 to 44 ages", "45 to 54 ages", "55 to 64 ages", "Total all ages"]

    def get_family_incomes(self):
        # Можно получить из таблицы или задать фиксированный список
        return self.query_single_column("SELECT DISTINCT family_income FROM demographic_income ORDER BY family_income")+["Все значения"]

    def get_categories(self):
        return self.query_single_column("SELECT DISTINCT category FROM demographic_expense ORDER BY category")+["Все значения"]

    def get_quintiles(self):
        return self.query_single_column("SELECT DISTINCT quintile FROM demographic_expense ORDER BY quintile")+["Все значения"]

    def query_single_column(self, query):
        try:
            conn = psycopg2.connect(host="localhost", database="Project", user="postgres", password="terramine")
            cur = conn.cursor()
            cur.execute(query)
            result = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            wx.MessageBox(f"Ошибка при выполнении запроса: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)
            return []

    def on_build_income(self, event):
        # Собираем параметры и формируем SQL-запрос
        sql = self.build_income_query()
        self.load_data(sql)

    def on_build_expense(self, event):
        sql = self.build_expense_query()
        self.load_data(sql)

    def build_income_query(self):
        # Формируем SQL-запрос для таблицы full_income с учетом фильтров
        filters = []

        # Регион
        region = self.income_region_choices.GetStringSelection()
        if region != "Все значения" and region:
            try:
                #region_id = int(region)
                filters.append(f"r.region = '{region}'")
            except ValueError:
                wx.MessageBox("Некорректное значение региона", "Ошибка", wx.OK | wx.ICON_ERROR)
        # Год
        year = self.income_year_choices.GetStringSelection()
        if year != "Все значения" and year:
            filters.append(f"y.year = {year}")
        # Возраст
        age = self.income_age_choices.GetStringSelection()
        if age != "Все значения" and age:
            filters.append(f"a_t.age = '{age}'")
        # Пол
        gender = self.income_gender_choices.GetStringSelection()
        if gender != "Все значения" and gender:
            filters.append(f"gt.gender = '{gender}'")
        # Доход семьи
        family_income = self.family_income_choices.GetStringSelection()
        if family_income != "Все значения" and family_income:
            filters.append(f"di.family_income = '{family_income}'")
        # Возраст старшего
        age_of_older = self.age_of_older_choices.GetStringSelection()
        if age_of_older != "Все значения" and age_of_older:
            filters.append(f"di.age_of_older = '{age_of_older}'")

        where_clause = " AND ".join(filters)
        if where_clause:
            where_clause = "WHERE " + where_clause

        sql = f"""
        SELECT
            fi.id,
            r.region AS province,
            y.year,
            di.age_of_older,
            di.family_income,
            di.family_type,
            m.uom,
            a_t.age,
            gt.gender,
            fi.income
        FROM full_income fi
        JOIN year y ON fi.year_id = y.id
        JOIN demographic_income di ON fi.demographic_id = di.id
        JOIN metrik m ON fi.id_stat = m.metrik_id
        JOIN age a ON fi.age_id = a.id
        JOIN age_table a_t ON a.age_id = a_t.id
        JOIN gender g ON fi.gender_id = g.id
        JOIN gender_table gt ON g.gender_id = gt.id
        JOIN region r ON a.region_id = r.region_id
        {where_clause}
        """

        return sql

    def build_expense_query(self):
        filters = []

        # Регион
        region = self.expense_region_choices.GetStringSelection()
        if region != "Все значения" and region:
            try:
                #region_id = int(region)
                filters.append(f"r.region = '{region}'")
            except ValueError:
                wx.MessageBox("Некорректное значение региона", "Ошибка", wx.OK | wx.ICON_ERROR)
        # Год
        year = self.expense_year_choices.GetStringSelection()
        if year != "Все значения" and year:
            filters.append(f"y.year = {year}")
        # Возраст
        age = self.expense_age_choices.GetStringSelection()
        if age != "Все значения" and age:
            filters.append(f"a_t.age = '{age}'")
        # Пол
        gender = self.expense_gender_choices.GetStringSelection()
        if gender != "Все значения" and gender:
            filters.append(f"gt.gender = '{gender}'")
        # Категория
        category = self.category_choices.GetStringSelection()
        if category != "Все значения" and category:
            filters.append(f"de.category = '{category}'")
        # Квинтиль
        quintile = self.quintile_choices.GetStringSelection()
        if quintile != "Все значения" and quintile:
            filters.append(f"de.quintile = '{quintile}'")
        where_clause = " AND ".join(filters)
        if where_clause:
            where_clause = "WHERE " + where_clause

        sql = f"""
        SELECT 
            ef.id,
            r.region as province,
            y.year,
            de.quintile,
            de.category,
            de.statistik,
            m.uom,
            a_t.age,
            gt.gender,
            ef.expense
        FROM full_expense ef
        JOIN demographic_expense de ON ef.demographic_id = de.id
        JOIN year y ON ef.year_id = y.id
        JOIN age a ON ef.age_id = a.id
        JOIN age_table a_t ON a.age_id = a_t.id
        JOIN gender g ON ef.gender_id = g.id
        JOIN gender_table gt ON g.gender_id = gt.id
        JOIN metrik m ON ef.id_stat = m.metrik_id
        JOIN region r ON g.region_id = r.region_id

        {where_clause}
        """

        return sql

    def load_data(self, sql):
        try:
            print("Executing SQL:\n", sql)  # Выводим SQL
            conn = psycopg2.connect(host="localhost", database="Project", user="postgres", password="terramine")
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            print(f"Fetched {len(rows)} rows")  # Количество полученных строк
            colnames = [desc[0] for desc in cursor.description]
            print(f"Columns: {colnames}")

            # Очистка грида
            row_count = self.grid.GetNumberRows()
            if row_count > 0:
                self.grid.DeleteRows(0, row_count)

            col_count = self.grid.GetNumberCols()
            if col_count > 0:
                self.grid.DeleteCols(0, col_count)

            # Добавление новых данных
            self.grid.AppendRows(len(rows))
            self.grid.AppendCols(len(colnames))
            for col_idx, col_name in enumerate(colnames):
                self.grid.SetColLabelValue(col_idx, col_name)

            # Заполнение таблицы данными
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except:
                            value = value.decode('utf-8', errors='replace')
                    self.grid.SetCellValue(row_idx, col_idx, str(value))
            self.grid.AutoSizeColumns()

            cursor.close()
            conn.close()
        except Exception as e:
            wx.MessageBox(f"Ошибка загрузки данных: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)

# Запуск
if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
