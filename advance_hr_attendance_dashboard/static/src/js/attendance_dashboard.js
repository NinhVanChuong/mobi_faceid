/* @odoo-module */
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AttendanceDashboard extends Component{
    setup(){
        this.action = useService('action')
        this.notification = useService("notification");
        // Lấy tháng hiện tại theo định dạng YYYY-MM
        const today = new Date();
        const currentMonth = today.toISOString().slice(0, 7); // Lấy YYYY-MM từ ISO string
        
        this.state = useState({
                        filteredDurationDates : [],
                        employeeData : [],
                        departments: [],
                        selectedDepartment: '',
                        selectedDuration: currentMonth,
                        isLoading: false,
                        searchTerm: ''
                    })
        this.orm = useService("orm");
        this.root = useRef('attendance-dashboard')
        this._loadDepartments();
    }

    async _loadDepartments() {
        try {
            // Lấy danh sách đơn vị con
            const childDepartments = await this.orm.call(
                'hr.department',
                'get_child_departments',
                [],
                {}
            );
            
            // Lấy thông tin đơn vị của người dùng hiện tại
            const currentUser = await this.orm.call(
                'hr.employee',
                'get_current_department',
                [],
                {}
            );
            
            if (currentUser && currentUser.department) {
                // Thêm đơn vị của người dùng vào đầu danh sách
                this.state.departments = [currentUser.department, ...childDepartments];
            } else {
                this.state.departments = childDepartments;
            }
        } catch (error) {
            console.error("Error loading departments:", error);
            this.notification.add(
                'Không thể tải danh sách phòng ban',
                {
                    type: 'danger',
                }
            );
        }
    }

    onChangeFilter(ev){
        ev.stopPropagation();
        const selectedMonth = ev.target.value;
        if (selectedMonth) {
            this.state.selectedDuration = selectedMonth;
        }
    }

    onChangeDepartment(ev) {
        const selectedName = ev.target.value;
        
        if (selectedName === "Tất cả đơn vị") {
            this.state.selectedDepartment = '';
            this.state.searchTerm = '';
            return;
        }

        // Tìm department dựa trên tên
        const department = this.state.departments.find(
            dept => dept.name === selectedName
        );
        
        if (department) {
            this.state.selectedDepartment = department.id.toString();
            this.state.searchTerm = department.name.toLowerCase();
        } else {
            // Nếu không tìm thấy, reset về "Tất cả đơn vị"
            this.state.selectedDepartment = '';
            this.state.searchTerm = '';
        }
    }

    onSearchDepartment(ev) {
        const searchValue = ev.target.value;
        this.state.searchTerm = searchValue.toLowerCase();
        
        // Nếu người dùng xóa hết text hoặc chọn "Tất cả đơn vị"
        if (!searchValue || searchValue === "Tất cả đơn vị") {
            this.state.selectedDepartment = '';
        }
    }

    get filteredDepartments() {
        if (!this.state.searchTerm) {
            return this.state.departments;
        }
        return this.state.departments.filter(dept => 
            dept.name.toLowerCase().includes(this.state.searchTerm)
        );
    }

    async onViewReport() {
        if (this.state.isLoading) return;

        this.state.isLoading = true;
        this.notification.add('Đang tải dữ liệu báo cáo...', {
            type: 'info',
        });

        try {
            await this._applyFilters();
            this.notification.add('Đã tải dữ liệu báo cáo thành công', {
                type: 'success',
            });
        } catch (error) {
            this.notification.add('Không thể tải dữ liệu báo cáo', {
                type: 'danger',
            });
            console.error('Error loading report:', error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async _applyFilters() {
        let params = {};
        if (this.state.selectedDuration) {
            params.duration = this.state.selectedDuration;
        }
        if (this.state.selectedDepartment) {
            params.department_id = this.state.selectedDepartment;
        }
        const result = await this.orm.call(
            "hr.employee",
            "get_employee_leave_data",
            [params]
        );
        this.state.filteredDurationDates = result.filtered_duration_dates;
        this.state.employeeData = result.employee_data;
    }

    //on clicking search button, employees will be filtered
    _OnClickSearchEmployee(ev){
        let searchbar = this.root.el.querySelector('#search-bar').value?.toLowerCase()
        var attendance_table_rows = this.root.el.querySelector('#attendance_table_nm').children[1]
        for (let tableData of attendance_table_rows.children){
            tableData.style.display = (!tableData.children[0].getAttribute("data-name").toLowerCase().includes(searchbar)) ? 'none':'';
        }
    }

    //on clicking Export Excel button, report will be exported
    async _OnClickExcelReport() {
        if (this.state.isLoading) return;

        this.state.isLoading = true;
        try {
            const params = {
                duration: this.state.selectedDuration,
                department_id: this.state.selectedDepartment,
                search_query: this.root.el.querySelector('#search-bar').value || false
            };
            
            const action = await this.orm.call(
                'hr.employee',
                'export_attendance_excel',
                [],
                { params: params }
            );
            
            if (action && action.url) {
                window.location = action.url;
            } else {
                throw new Error('Invalid action response');
            }
        } catch (error) {
            console.error('Error exporting Excel:', error);
            this.notification.add(
                'Không thể xuất file Excel',
                {
                    type: 'danger',
                }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    formatDate(inputDate) {
        const months = [
            'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ];
        const parts = inputDate.split('-');
        const day = parts[2];
        const month = months[parseInt(parts[1], 10) - 1];
        const year = parts[0];
        return `${day}-${month}-${year}`;
    }
}
AttendanceDashboard.template = 'AttendanceDashboard';
registry.category("actions").add("attendance_dashboard", AttendanceDashboard);
