# Copyright (c) 2024, Precihole Sports Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DelayEntry(Document):
	def on_submit(self):
		self.process_late_entries()

	def process_late_entries(self):
		deduction_type = self.get_deduction_type()
		if not deduction_type or deduction_type == 'No Deduction':
			return

		minimum_late_days = self.get_minimum_late_days()
		if minimum_late_days <= 0:
			return

		try:
			active_employees = self.get_active_employees()
			for employee in active_employees:
				total_deductions = self.calculate_absent_days(employee['name'], minimum_late_days)
				if total_deductions > 0:
					self.mark_absence(employee['name'], total_deductions)
		except Exception as e:
			frappe.log_error(message=str(e), title="Error in process_late_entries")

	def get_deduction_type(self):
		return frappe.db.get_single_value('Delay Pay Settings', 'deduction_type')

	def get_minimum_late_days(self):
		return frappe.db.get_single_value('Delay Pay Settings', 'minimum_late_days') or 0

	def get_salary_deduction_days(self):
		return frappe.db.get_single_value('Delay Pay Settings', 'salary_deduction_days')

	def get_active_employees(self):
		return frappe.db.get_all('Employee', {'status': 'Active'})

	def calculate_absent_days(self, employee_id, allowed_late_days):
		attendance_records = self.get_late_attendance_records(employee_id)
		total_late_count = len(attendance_records)

		return self.calculate_absent_days_based_on_late_count(total_late_count, allowed_late_days)

	def get_late_attendance_records(self, employee_id):
		return frappe.get_all('Attendance', filters={
			'employee': employee_id,
			'docstatus': 1,
			'attendance_date': ['between', [self.start_date, self.end_date]],
			'late_entry': 1
		})

	def calculate_absent_days_based_on_late_count(self, total_late_count, allowed_late_days):
		eligible_late_count = total_late_count // allowed_late_days
		total_deductions = eligible_late_count * self.get_salary_deduction_days()
		return total_deductions

	def mark_absence(self, employee_id, absent_days):
		whole_days = int(absent_days)
		half_days = absent_days - whole_days

		if half_days > 0:
			self.mark_half_days(employee_id, half_days)
		if whole_days > 0:
			self.mark_full_days_absent(employee_id, whole_days)

	def mark_half_days(self, employee_id, half_days):
		last_attendance = self.get_last_present_attendance(employee_id)
		if last_attendance:
			frappe.db.set_value('Attendance', last_attendance[0]['name'], {'status': 'Half Day', 'adjust_salary_deduction': 1, 'delay_entry': self.name}, update_modified=False)

	def get_last_present_attendance(self, employee_id):
		return frappe.get_all('Attendance', filters={
			'employee': employee_id,
			'status': 'Present',
			'docstatus': 1,
			'attendance_date': ['between', [self.start_date, self.end_date]]
		}, order_by='attendance_date desc', limit=1)

	def mark_full_days_absent(self, employee_id, whole_days):
		attendance_records = self.get_present_attendance_records(employee_id, whole_days)
		if attendance_records:
			frappe.db.set_value('Attendance', attendance_records, {'status': 'Absent', 'adjust_salary_deduction': 1, 'delay_entry': self.name}, update_modified=False)

	def get_present_attendance_records(self, employee_id, limit):
		return frappe.get_all('Attendance', filters={
			'employee': employee_id,
			'status': 'Present',
			'docstatus': 1,
			'attendance_date': ['between', [self.start_date, self.end_date]]
		}, order_by='attendance_date desc', limit=limit, pluck='name')
