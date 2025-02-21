# inventory_assistant/simulation/engine.py
from datetime import datetime, timedelta
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from inventory_assistant.database.db import Database
from inventory_assistant.simulation.generator import DataGenerator
from inventory_assistant.models.laptop import WarehouseStock, Laptop
from inventory_assistant.config import LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, LOG_FILE


# Set up logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimulationEngine:
    def __init__(self, db: Database):
        self.db = db
        self.generator = DataGenerator()
        self.current_date = datetime.now()
        self.laptops = []
        self.console = Console()

    def print_daily_report(self, transactions):
        """Print formatted daily report"""
        self.console.print(f"\n[bold blue]Day Report: {self.current_date.date()}[/bold blue]")
        
        with self.db.session() as session:
            # Transaction Summary
            if transactions:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Model ID")
                table.add_column("Warehouse")
                table.add_column("Quantity")
                
                for trans in transactions:
                    table.add_row(
                        trans.model_id,
                        trans.warehouse_id,  # Already a string
                        str(trans.quantity)
                    )
                
                self.console.print(Panel.fit(table, title="Daily Transactions"))
            else:
                self.console.print("[yellow]No transactions today[/yellow]")

            # Stock Levels
            stock_table = Table(show_header=True, header_style="bold green")
            stock_table.add_column("Model ID")
            stock_table.add_column("Warehouse")
            stock_table.add_column("Quantity")
            stock_table.add_column("Min Stock")
            
            stocks = session.query(WarehouseStock).all()
            for stock in stocks:
                laptop = session.query(Laptop).filter_by(model_id=stock.model_id).first()
                if laptop:
                    color = "[red]" if stock.quantity < laptop.min_stock else "[green]"
                    stock_table.add_row(
                        stock.model_id,
                        stock.warehouse_id,  # Already a string
                        f"{color}{stock.quantity}[/]",
                        str(laptop.min_stock)
                    )
            
            self.console.print(Panel.fit(stock_table, title="Current Stock Levels"))

    def initialize_simulation(self):
        """Set up initial simulation state"""
        self.console.print("[bold green]Initializing Simulation...[/bold green]")
        
        # Generate laptop models
        generated_laptops = self.generator.generate_laptop_models()
        
        # Store laptops and keep track of them in the session
        with self.db.session() as session:
            for laptop in generated_laptops:
                session.add(laptop)
                self.console.print(f"Created laptop model: {laptop.brand.value} {laptop.model_name}")
            
            # Generate initial stock
            initial_stocks = self.generator.generate_initial_stock(generated_laptops)
            for stock in initial_stocks:
                session.add(stock)
            
            # Commit everything
            session.commit()
            
            # Store laptops for future reference
            self.laptops = generated_laptops.copy()

        self.console.print("[bold green]Initial stock generated![/bold green]")
        # Print initial stock levels
        self.print_daily_report([])

    def advance_day(self):
        """Simulate one day of operations"""
        self.current_date += timedelta(days=1)
        
        with self.db.session() as session:
            current_laptops = session.query(Laptop).all()
            daily_transactions = self.generator.generate_daily_transactions(
                current_laptops, 
                self.current_date
            )
            
            # Update stock levels based on transactions
            for transaction in daily_transactions:
                session.add(transaction)
                
                stock = session.query(WarehouseStock).filter_by(
                    model_id=transaction.model_id,
                    warehouse_id=transaction.warehouse_id
                ).first()
                
                if stock:
                    new_quantity = stock.quantity + transaction.quantity  # Adding negative quantity = subtraction
                    if new_quantity >= 0:  # Check if we have enough stock
                        stock.quantity = new_quantity
                        stock.updated_at = self.current_date
                    else:
                        # If not enough stock, adjust transaction to available stock
                        transaction.quantity = -stock.quantity  # Take all remaining stock
                        stock.quantity = 0
            
            session.commit()
            
            # Print daily report
            self.print_daily_report(daily_transactions)

    def run_simulation(self, days: int):
        """Run simulation for specified number of days"""
        self.console.print(f"\n[bold]Starting {days} day simulation...[/bold]")
        for day in range(days):
            self.console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
            self.console.print(f"[bold]Day {day + 1} of {days}[/bold]")
            self.advance_day()