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
                        selectedDepartments: [], // Thay đổi từ selectedDepartment thành selectedDepartments (array)
                        selectedDuration: currentMonth,
                        isLoading: false,
                        searchTerm: '',  // Thêm searchTerm cho tìm kiếm phòng ban
                        selectedDepartmentNames: [] // Thêm để lưu tên các đơn vị đã chọn
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

    // Thêm hàm để xử lý chọn/bỏ chọn đơn vị
    onToggleDepartment(departmentId, departmentName) {
        const index = this.state.selectedDepartments.indexOf(departmentId);
        const nameIndex = this.state.selectedDepartmentNames.indexOf(departmentName);
        
        if (index > -1) {
            // Bỏ chọn đơn vị
            this.state.selectedDepartments.splice(index, 1);
            this.state.selectedDepartmentNames.splice(nameIndex, 1);
        } else {
            // Chọn đơn vị
            this.state.selectedDepartments.push(departmentId);
            this.state.selectedDepartmentNames.push(departmentName);
        }
    }

    // Hàm để xóa tất cả đơn vị đã chọn
    onClearAllDepartments() {
        this.state.selectedDepartments = [];
        this.state.selectedDepartmentNames = [];
        this.state.searchTerm = '';
    }

    // Hàm để kiểm tra đơn vị có được chọn hay không
    isDepartmentSelected(departmentId) {
        return this.state.selectedDepartments.includes(departmentId);
    }

    // Hàm để kiểm tra tất cả đơn vị có được chọn hay không
    areAllDepartmentsSelected() {
        if (this.filteredDepartments.length === 0) return false;
        return this.filteredDepartments.every(dept => 
            this.state.selectedDepartments.includes(dept.id)
        );
    }

    // Hàm để chọn/bỏ chọn tất cả đơn vị
    onToggleAllDepartments() {
        const allSelected = this.areAllDepartmentsSelected();
        
        if (allSelected) {
            // Bỏ chọn tất cả đơn vị đang hiển thị
            this.filteredDepartments.forEach(dept => {
                const index = this.state.selectedDepartments.indexOf(dept.id);
                const nameIndex = this.state.selectedDepartmentNames.indexOf(dept.name);
                if (index > -1) {
                    this.state.selectedDepartments.splice(index, 1);
                }
                if (nameIndex > -1) {
                    this.state.selectedDepartmentNames.splice(nameIndex, 1);
                }
            });
        } else {
            // Chọn tất cả đơn vị đang hiển thị
            this.filteredDepartments.forEach(dept => {
                if (!this.state.selectedDepartments.includes(dept.id)) {
                    this.state.selectedDepartments.push(dept.id);
                }
                if (!this.state.selectedDepartmentNames.includes(dept.name)) {
                    this.state.selectedDepartmentNames.push(dept.name);
                }
            });
        }
    }

    onChangeDepartment(ev) {
        const selectedName = ev.target.value;
        
        if (selectedName === "Tất cả đơn vị") {
            this.onClearAllDepartments();
            return;
        }

        // Tìm department dựa trên tên
        const department = this.state.departments.find(
            dept => dept.name === selectedName
        );
        
        if (department) {
            this.onToggleDepartment(department.id, department.name);
        }
    }

    onSearchDepartment(ev) {
        const searchValue = ev.target.value;
        this.state.searchTerm = searchValue.toLowerCase();
        
        // Nếu người dùng xóa hết text, không reset selectedDepartments
        if (!searchValue) {
            this.state.searchTerm = '';
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
        if (this.state.selectedDepartments.length > 0) {
            params.department_ids = this.state.selectedDepartments; // Thay đổi thành department_ids
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
                department_ids: this.state.selectedDepartments.length > 0 ? this.state.selectedDepartments : false, // Thay đổi thành department_ids
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
