#!/usr/bin/env python
#coding=UTF8
'''

'''

import sys

reload(sys)

class Flight():
    def __init__(self):
        self.flight_no = 'NULL'
        self.plane_no = 'NULL'
        self.airline = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.real_class = 'NULL'
        self.package = 'NULL'
        self.stop_airport = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.stop_dur = 'NULL'
        self.daydiff = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop_cost = 'NULL'
        self.stop = -1
        self.plane_type = 'NULL'
        self.plane_corp = 'NULL'
        self.flight_corp = 'NULL'
        self.change_rule = 'NULL'
        self.share_flight = 'NULL'
        self.stopby = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.others_info = 'NULL'
        self.ticket_type = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results

    def to_tuple(self):
        return (self.flight_no, self.plane_type, self.flight_corp, self.dept_id,\
                self.dest_id, self.dept_day, self.dept_time, self.dest_time, self.dur,\
                self.rest, self.price, self.tax, self.surcharge, self.promotion, self.currency,\
                self.seat_type, self.real_class, self.package, self.stop_id, self.stop_time,\
                self.daydiff, self.source, self.return_rule, self.change_rule, self.stop,\
                self.share_flight, self.stopby, self.baggage, self.transit_visa,\
                self.reimbursement, self.flight_meals, self.ticket_type, self.others_info)

class MultiFlight():
    def __init__(self):
        self.flight_no = 'NULL'
        self.plane_no = 'NULL'
        self.airline = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.real_class = 'NULL'
        self.package = 'NULL'
        self.stop_airport = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.stop_dur = 'NULL'
        self.daydiff = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop_cost = 'NULL'
        self.stop = -1
        self.plane_type = 'NULL'
        self.plane_corp = 'NULL'
        self.flight_corp = 'NULL'
        self.change_rule = 'NULL'
        self.share_flight = 'NULL'
        self.stopby = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.others_info = 'NULL'
        self.ticket_type = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results

    def to_tuple(self):
        return (self.flight_no, self.plane_type, self.flight_corp, self.dept_id,
                self.dest_id, self.dept_day, self.dept_time, self.dest_time, self.dur,
                self.rest, self.price, self.tax, self.surcharge, self.promotion, self.currency,
                self.seat_type, self.real_class, self.package, self.stop_id, self.stop_time,
                self.daydiff, self.source, self.return_rule, self.change_rule, self.stop,
                self.share_flight, self.stopby, self.baggage, self.transit_visa,
                self.reimbursement, self.flight_meals, self.ticket_type, self.others_info)


class RoundFlight():
    def __init__(self):
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dest_day = 'NULL'
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.flight_no_A = 'NULL'
        self.airline_A = 'NULL'
        self.plane_no_A = 'NULL'
        self.dept_time_A = 'NULL'
        self.dest_time_A = 'NULL'
        self.dur_A = -1
        self.seat_type_A = 'NULL'
        self.real_class_A = 'NULL'
        self.stop_id_A = 'NULL'
        self.stop_time_A = 'NULL'
        self.daydiff_A = 'NULL'
        self.stop_A = -1
        self.flight_no_B = 'NULL'
        self.airline_B = 'NULL'
        self.plane_no_B = 'NULL'
        self.dept_time_B = 'NULL'
        self.dest_time_B = 'NULL'
        self.dur_B = -1
        self.seat_type_B = 'NULL'
        self.real_class_B = 'NULL'
        self.stop_id_B = 'NULL'
        self.stop_time_B = 'NULL'
        self.daydiff_B = 'NULL'
        self.stop_B = -1
        self.change_rule = 'NULL'
        self.share_flight_A = 'NULL'
        self.share_flight_B = 'NULL'
        self.stopby_A = 'NULL'
        self.stopby_B = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.ticket_type = 'NULL'
        self.others_info = 'NULL'
        self.rest = -1

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode('UTF-8')))
        return results

    def to_tuple(self):
        return (self.dept_id, self.dest_id, self.dept_day,
                self.dest_day, self.price, self.tax, self.surcharge,
                self.promotion, self.currency, self.source,
                self.return_rule, self.flight_no_A, self.airline_A,
                self.plane_no_A, self.dept_time_A, self.dest_time_A,
                self.dur_A, self.seat_type_A, self.real_class_A,
                self.stop_id_A, self.stop_time_A, self.daydiff_A,
                self.stop_A, self.flight_no_B, self.airline_B,
                self.plane_no_B, self.dept_time_B, self.dest_time_B,
                self.dur_B, self.seat_type_B, self.real_class_B,
                self.stop_id_B,self.stop_time_B, self.daydiff_B,
                self.stop_B, self.change_rule, self.share_flight_A,
                self.share_flight_B, self.stopby_A, self.stopby_B,
                self.baggage, self.transit_visa, self.reimbursement,
                self.flight_meals, self.ticket_type,
                self.others_info, self.rest)


class EachFlight():
    def __init__(self):
        self.flight_key = 'NULL'
        self.flight_no = 'NULL'
        self.airline = 'NULL'
        self.plane_no = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.daydiff = -1
        self.stop = -1
        self.cost = -1
        self.schedule = 'NULL'
        self.source = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode('UTF-8')))

        return results

class Hotel():
    def __init__(self):
        self.hotel_name = 'NULL'
        self.hotel_name_en = 'NULL'
        self.source = 'NULL'
        self.source_id = 'NULL'
        self.brand_name = 'NULL'
        self.map_info = 'NULL'
        self.address = 'NULL'
        self.city = 'NULL'
        self.country = 'NULL'
        self.postal_code = 'NULL'
        self.star = -1.0
        self.grade = 'NULL'
        self.review_num = -1
        self.has_wifi = 'NULL'
        self.is_wifi_free = 'NULL'
        self.has_parking = 'NULL'
        self.is_parking_free ='NULL'
        self.service = 'NULL'
        self.img_items = 'NULL'
        self.description = 'NULL'
        self.accepted_cards = 'NULL'
        self.check_in_time = 'NULL'
        self.check_out_time = 'NULL'
        self.hotel_url = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Room():
    def __init__(self):
        self.hotel_name = 'NULL'
        self.city = 'NULL'
        self.source = 'NULL'
        self.source_hotelid = 'NULL'
        self.source_roomid = 'NULL'
        self.room_type = 'NULL'
        self.real_source = 'NULL'
        self.occupancy = -1
        self.bed_type = 'NULL'
        self.size = -1.0
        self.floor = -1
        self.check_in = 'NULL'
        self.check_out = 'NULL'
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.currency = 'NULL'
        self.is_extrabed = 'NULL'
        self.is_extrabed_free = 'NULL'
        self.has_breakfast = 'NULL'
        self.is_breakfast_free = 'NULL'
        self.is_cancel_free = 'NULL'
        self.room_desc = 'NULL'
        self.return_rule = 'NULL'
        self.pay_method = 'NULL'
        self.extrabed_rule = 'NULL'
        self.change_rule = 'NULL'
        self.others_info = 'NULL'
        self.guest_info = 'NULL'
        self.hotel_url = 'NULL'


    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Comment():
    def __init__(self):
        self.hotel_name = 'NULL'
        self.city = 'NULL'
        self.source_hotelid = 'NULL'
        self.comment = 'NULL'
        self.comment_user = 'NULL'
        self.source = 'NULL'
        self.title = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Attraction():
    def __init__(self):
        self.name = 'NULL'
        self.name_en = 'NULL'
        self.grade = 'NULL'
        self.city_id = 'NULL'
        self.map_info = 'NULL'
        self.address = 'NULL'
        self.phone = 'NULL'
        self.website = 'NULL'
        self.open = 'NULL'
        self.close = 'NULL'
        self.ticket = 'NULL'
        self.description = 'NULL'
        self.image = 'NULL'
        self.rcmd_visit_time = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Train():
    def __init__(self):
        self.train_no = 'NULL'
        self.train_type = 'NULL'
        self.train_corp = 'NULL'
        self.dept_city = 'NULL'
        self.dept_station = 'NULL'
        self.dest_city = 'NULL'
        self.dest_station = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.price = -1.0
        self.tax = -1.0
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop = -1
        self.stop_station = 'NULL'
        self.dept_day = 'NULL'
        self.real_class = 'NULL'
        self.stopid = 'NULL'
        self.stoptime = 'NULL'
        self.daydiff = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.change_rule = 'NULL'
        self.train_facilities = 'NULL'
        self.ticket_info = 'NULL'
        self.electric_ticket = 'NULL'
        self.promotion = 'NULL'
        self.others_info = 'NULL'
        self.change_rule = 'NULL'
        self.facilities = 'NULL'
        self.ticket_type = 'NULL'
        self.rest = -1

    def to_tuple(self):
        return (self.train_no, self.train_type, \
                self.train_corp, self.dept_city, self.dept_id, \
                self.dest_city, self.dest_id, self.dept_day, \
                self.dept_time, self.dest_time, self.dur, \
                self.price, self.tax, self.currency, self.seat_type, \
                self.real_class, self.promotion, self.source, \
                self.return_rule, self.change_rule, self.stopid, \
                self.stoptime, self.daydiff, self.stop, \
                self.train_facilities, self.ticket_type, \
                self.electric_ticket, self.others_info, self.rest)


    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results



class EachTrain():
    def __init__(self):
        self.train_key = 'NULL'
        self.train_no = 'NULL'
        self.train_corp = 'NULL'
        self.train_type = 'NULL'
        self.dept_station = 'NULL'
        self.dest_station = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))

        return results


class Car():
    def __init__(self):
        self.source = 'NULL'
        self.company = 'NULL'
        self.car_type = 'NULL'
        self.car_desc = 'NULL'
        self.car_image = 'NULL'
        self.price = -1.0
        self.list_price = -1.0
        self.rest = -1
        self.currency = 'NULL'
        self.rent_city = 'NULL'
        self.return_city = 'NULL'
        self.rent_store = 'NULL'
        self.return_store = 'NULL'
        self.rent_time = 'NULL'
        self.return_time = 'NULL'
        self.store_name = 'NULL'
        self.store_addr = 'NULL'
        self.return_store_name = 'NULL'
        self.return_store_addr = 'NULL'
        self.take_time = 'NULL'
        self.return_time = 'NULL'
        self.rent_time = 'NULL'
        self.rent_area = 'NULL'
        self.return_area = 'NULL'
        self.is_automatic = 'NULL'
        self.baggages = 'NULL'
        self.passengers = -1
        self.pay_method = 'NULL'
        self.insurance = 'NULL'
        self.fuel_strategy = 'NULL'
        self.promotion = 'NULL'
        self.license = 'NULL'
        self.diff_location_fee = -1.0
        self.door_num = -1
        self.mile_limit = 'NULL'
        self.extra_driver = 'NULL'
        self.zone_desc = 'NULL'
        self.package = 'NULL'

    def items(self):
        results = []
        for k,v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results

class CarStore():
    def __init__(self):
        self.store_id = 'NULL'
        self.company = 'NULL'
        self.store_code = 'NULL'
        self.store_name = 'NULL'
        self.open_time =  'NULL'
        self.close_time = 'NULL'
        self.address = 'NULL'
        self.area = 'NULL'
        self.area_code = 'NULL'
        self.telephone = 'NULL'
        self.map_info = 'NULL'
        self.city_id = 'NULL'


    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Bus():

    def __init__(self):
        self.dept_city = 'NULL'
        self.dest_city = 'NULL'
        self.dept_station = 'NULL'
        self.dest_station = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.price = -1.0
        self.currency = 'NULL'
        self.source = 'NULL'
        self.corp = 'NULL'
        self.tax = -1.0
        self.return_rule = 'NULL'
        self.daydiff = 'NULL'
        self.rest = -1
        self.change_rule = 'NULL'
        self.ticket_type = 'NULL'
        self.bus_type = 'NULL'
        self.insurance = -1.0
        self.service_fee = -1.0
        self.stop = -1
        self.bus_no = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.transfer_interval = 'NULL'
        self.has_wifi = 'NULL'
        self.has_charge = 'NULL'
        self.has_extended_seat = 'NULL'
        self.free_baggage_num = 'NULL'
        self.free_baggage_weight = 'NULL'
        self.has_meals = 'NULL'
        self.has_wc = 'NULL'
        self.arrive_gate = 'NULL'

    def item(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Pickup():
    def __init__(self):
        self.source = 'NULL'
        self.pattren_type = 'NULL'
        self.airport_code = 'NULL'

        self.dept_addr = 'NULL'
        self.dept_lat = 'NULL'
        self.dept_lng = 'NULL'
        self.dest_addr = 'NULL'
        self.dest_lat = 'NULL'
        self.dest_lng = 'NULL'

        self.use_time = 'NULL'

        self.car_type_id = 'NULL'
        self.car_title = 'NULL'
        self.car_desc = 'NULL'
        self.car_seat_num = -1
        self.car_luggage_num = -1

        self.price = -1.0
        self.currency = 'NULL'
        self.price_mark = 'NULL'

        self.is_support_card = 'NULL'
        self.card_fee = -1.0
        self.is_support_child_seat = 'NULL'
        self.child_seat_fee = -1.0
        self.is_has_car_wifi = 'NULL'
        self.car_wifi_fee = -1.0

        self.is_must_child_seat = 'NULL'
        self.is_support_chinese = 'NULL'

    def item(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results
