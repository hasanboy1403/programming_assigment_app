import psycopg2

class DatabaseConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host="aws-db.ctbwu5xukfqx.eu-north-1.rds.amazonaws.com",
                database="daraja_db",
                user="postgres",
                password="hasanboy1403"
            )
            self.cursor = self.conn.cursor()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def execute_query(self, query, values=None, fetch=False):
        try:
            self.cursor.execute(query, values)
            if fetch:
                return self.cursor.fetchall()
            else:
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error while executing query", error)
            return None

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

class CustomerOrder:
    def __init__(self, db):
        self.selected_foods = []
        self.db = db
        self.run_console_app()

    def fetch_food_items(self):
        query = "SELECT food_name, food_description, price FROM menu"
        return self.db.execute_query(query, fetch=True)

    def fetch_table_info(self):
        query = "SELECT table_number, category FROM tables"
        return self.db.execute_query(query, fetch=True)

    def submit_order(self, name, table, table_category):
        try:
            query = "INSERT INTO customer (name, tables, food, total_price) VALUES (%s, %s, %s, %s) RETURNING id, food, tables, total_price"
            selected_food_names = [f[0] for f in self.selected_foods]
            total_price = sum([f[2] for f in self.selected_foods])
            if table_category == 'A':
                total_price *= 1.10
            values = (name, table, ', '.join(selected_food_names), total_price)
            result = self.db.execute_query(query, values, fetch=True)
            if result:
                order_id, food, tables, total_price = result[0]
                print("Order submitted successfully")
                print(f"Total Price: ${total_price:.2f}")
                print("Your Recipe:")
                print(f"Order ID: {order_id}")
                print(f"Food: {food}")
                print(f"Tables: {tables}")
                print(f"Total Price: ${total_price:.2f}")
            else:
                print("Failed to submit order.")
        except (Exception, psycopg2.Error) as error:
            print("Error while submitting order:", error)

    def make_order(self):
        name = input("Enter your name: ")

        print("\nSelect food items (input the number, max 10 items, input 'done' to finish):")
        foods = self.fetch_food_items()
        for idx, (food_name, food_description, price) in enumerate(foods, 1):
            print('---------------------------------------------------------')
            print(f"{idx}. {food_name} - {food_description} - {price:.2f}")
            print('---------------------------------------------------------')

        while len(self.selected_foods) < 10:
            choice = input("Select a food item: ")
            if choice.lower() == 'done':
                break
            if choice.isdigit() and 1 <= int(choice) <= len(foods):
                self.selected_foods.append(foods[int(choice) - 1])
            else:
                print("Invalid choice. Try again.")

        print("\nSelect a table:")
        tables = self.fetch_table_info()
        for idx, (table_number, category) in enumerate(tables, 1):
            print(f"{idx}. Table {table_number} - Category {category}")
        table_choice = input("Select a table: ")
        if table_choice.isdigit() and 1 <= int(table_choice) <= len(tables):
            table = tables[int(table_choice) - 1][0]
            table_category = tables[int(table_choice) - 1][1]
        else:
            print("Invalid choice. Defaulting to first table.")
            table = tables[0][0]
            table_category = tables[0][1]

        self.submit_order(name, table, table_category)

    def my_order(self):
        order_id = input("Enter your order ID: ")
        query = "SELECT name, tables, food, total_price FROM customer WHERE id = %s"
        result = self.db.execute_query(query, (order_id,), fetch=True)
        if result:
            name, table, food, total_price = result[0]
            print("\nYour Order:")
            print("+------------+--------+---------------------+-------------+")
            print(f"| Name       | Table  | Food                | Total Price |")
            print("+------------+--------+---------------------+-------------+")
            print(f"| {name:<10} | {table:<6} | {food:<20} | {total_price:>11.2f} |")
            print("+------------+--------+---------------------+-------------+")

            delete_choice = input("Do you want to delete this order? (yes/no): ")
            if delete_choice.lower() == "yes":
                delete_query = "DELETE FROM customer WHERE id = %s"
                self.db.execute_query(delete_query, (order_id,))
                print("Order deleted successfully")
            else:
                print("Deletion canceled")
        else:
            print("Order not found.")

    def run_console_app(self):
        while True:
            print("\nCustomer Menu:")
            print("1. Make Order")
            print("2. My Order")
            print("3. Exit")
            choice = input("Choose an option: ")

            if choice == '1':
                self.make_order()
            elif choice == '2':
                self.my_order()
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")


class Manager:
    def __init__(self, db):
        self.db = db
        self.logged_in = False
        self.run_console_app()

    def add_food(self):
        food_name = input("Enter food name: ")
        food_description = input("Enter food description: ")
        price = input("Enter price: ")
        query = "INSERT INTO menu (food_name, food_description, price) VALUES (%s, %s, %s)"
        self.db.execute_query(query, (food_name, food_description, price))
        print("Food added successfully")

    def add_table(self):
        table_number = input("Enter table number: ")
        category = input("Enter category: ")
        query = "INSERT INTO tables (table_number, category) VALUES (%s, %s)"
        self.db.execute_query(query, (table_number, category))
        print("Table added successfully")

    def view_order_list(self):
        try:
            query = "SELECT name, tables, food, total_price FROM customer"
            orders = self.db.execute_query(query, fetch=True)
            if orders is not None:  
                print("\nOrder List:")
                print("+------------+--------+---------------------+-------------+")
                print("|   Name     | Table  |        Food         | Total Price |")
                print("+------------+--------+---------------------+-------------+")
                for name, tables, food, total_price in orders:
                    print(f"| {name:<10} | {tables:<6} | {food:<20} | {total_price:>11.2f} |")
                print("+------------+--------+---------------------+-------------+")
            else:
                print("No orders found.")
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching order list:", error)


    def view_food_list(self):
        try:
            self.db.connect()  
            cursor = self.db.cursor
            query = "SELECT food_name FROM menu"
            cursor.execute(query)
            foods = cursor.fetchall()
            if foods:
                print("\nFood List:")
                print("+----+----------------------+")
                print("| ID |      Food Name       |")
                print("+----+----------------------+")
                for index, food in enumerate(foods, start=1):
                    print(f"| {index:2d} | {food[0]:20} |")
                print("+----+----------------------+")

                while True:
                    choice = input("Enter the number of the food item to delete (0 to cancel): ")
                    if choice.isdigit():
                        choice = int(choice)
                        if 0 < choice <= len(foods):
                            confirm = input(f"Are you sure you want to delete '{foods[choice-1][0]}'? (yes/no): ")
                            if confirm.lower() == "yes":
                                delete_query = "DELETE FROM menu WHERE food_name = %s"
                                cursor.execute(delete_query, (foods[choice-1][0],))
                                self.db.conn.commit()
                                print("Food item deleted successfully")
                            else:
                                print("Deletion canceled")
                            break
                        elif choice == 0:
                            print("Deletion canceled")
                            break
                        else:
                            print("Invalid choice. Please enter a valid number.")
                    else:
                        print("Invalid input. Please enter a number.")
            else:
                print("No food items found")
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL:", error)
            print("Failed to fetch food items")


    def login(self):
        while not self.logged_in:
            username = input("Enter manager username: ")
            password = input("Enter manager password: ")

            query = "SELECT * FROM manager WHERE username = %s AND password = %s"
            result = self.db.execute_query(query, (username, password), fetch=True)

            if result:
                print("Login successful!")
                self.logged_in = True
            else:
                print("Invalid username or password. Please try again.")

    def update_food(self):
        try:
            query = "SELECT id, food_name FROM menu"
            foods = self.db.execute_query(query, fetch=True)
            if foods:
                print("\nSelect a food item to update:")
                for food_id, food_name in foods:
                    print(f"{food_id}. {food_name}")
                choice = input("Enter the ID of the food item to update: ")
                if choice.isdigit() and int(choice) in [food[0] for food in foods]:
                    food_id = int(choice)
                    new_name = input("Enter the new name for the food item: ")
                    new_description = input("Enter the new description for the food item: ")
                    new_price = input("Enter the new price for the food item: ")
                    update_query = "UPDATE menu SET food_name = %s, food_description = %s, price = %s WHERE id = %s"
                    self.db.execute_query(update_query, (new_name, new_description, new_price, food_id))
                    print("Food item updated successfully")
                else:
                    print("Invalid choice. Please enter a valid food item ID.")
            else:
                print("No food items found")
        except (Exception, psycopg2.Error) as error:
            print("Error while updating food item:", error)

    def run_console_app(self):
        if not self.logged_in:
            print("You must log in first.")
            return

        while True:
            print("\nManager Menu:")
            print("1. Add Food")
            print("2. Add Table")
            print("3. View Order List")
            print("4. View Food List")
            print("5. Update Food")
            print("6. Exit")
            choice = input("Choose an option: ")

            if choice == '1':
                self.add_food()
            elif choice == '2':
                self.add_table()
            elif choice == '3':
                self.view_order_list()
            elif choice == '4':
                self.view_food_list()
            elif choice == '5':
                self.update_food()
            elif choice == '6':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    db = DatabaseConnection()
    while True:
        print("\nMain Menu:")
        print("1. Customer")
        print("2. Manager")
        print("3. Exit")
        user_choice = input("Choose an option: ")

        if user_choice == '1':
            CustomerOrder(db)
        elif user_choice == '2':
            manager = Manager(db)
            manager.login()
            if manager.logged_in:
                manager.run_console_app()
        elif user_choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
