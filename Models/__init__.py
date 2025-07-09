from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from Models.Employee import Employees
from Models.Schedules import Employee_schedules, Employee_available_schedules
from Models.Vechile  import VechileDetails
from Models.Route.Routing import PickupRoutingWithAllEmployees, DropRoutingWithAllEmployess
from Models.Route.Cluster import ManualClusteredPickupData
from Models.Route.Cluster import ManualClusteredDropData
from Models.TripBilling import PickupTripBillings, DropTripBillings
from Models.TripBilling import BillingPolicies
from Models.Logs import EmployeeSchedulesLogs
from Models.TripBilling import PickupTripEmployeeLink, DropTripEmployeeLink