from flask import Blueprint

home = Blueprint('home', __name__)

from .Route.Clusturing import Pickup_cluster_routing
from .Route.Clusturing import Drop_cluster_routing
from .Route.FinalRoutingDetails import Routing
from .Route.RouteOptimizing import RoutingOptimzation
from .Employee import Employees
from .Schedules import Employee_available_schedules, Employees_schedules
from .Vechile import VechileDetails
from .Vechile import RoutingVechileUpdate
from .TripBilling import PickupTripBillings, DropTripBillings, BillingPolicies, TripBillingReports
from .Route.RouteOptimizing import PIckuproutingOTPVerify, DropRoutingOTPVerify


