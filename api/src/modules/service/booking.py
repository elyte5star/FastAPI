from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.booking import CreateBookingRequest
from modules.repository.response_models.booking import CreateBookingResponse


class BookingHandler(ProductQueries):
    
    def _create_booking(self,req:CreateBookingRequest)->CreateBookingResponse:
        pass