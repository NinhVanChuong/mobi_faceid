/** @odoo-module */
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatDate } from "@web/core/l10n/dates";

class AttendanceReportDaily extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.state = useState({
            departments: [],
            employeeData: [],
            selectedDepartments: [], // Thay đổi từ selectedDepartment thành selectedDepartments (array)
            selectedDate: this._getVietnamToday(),
            selectedStatus: [],
            searchQuery: '',
            isLoading: false,
            searchTerm: '',  // Thêm searchTerm cho tìm kiếm phòng ban
            selectedDepartmentNames: [] // Thêm để lưu tên các đơn vị đã chọn
        });
        this.loadDepartments();
    }

    _getVietnamToday() {
        const now = new Date();
        const vietnamTime = new Date(now.getTime() + (7 * 60 * 60 * 1000));
        return vietnamTime.toISOString().split('T')[0];
    }

    async loadDepartments() {
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

    async loadEmployeeData() {
        if (this.state.isLoading) return;

        this.state.isLoading = true;
        try {
            const params = {
                selected_date: this.state.selectedDate,
                department_ids: this.state.selectedDepartments.length > 0 ? this.state.selectedDepartments : false, // Thay đổi thành department_ids
                status: this.state.selectedStatus,
                search_query: this.state.searchQuery || false
            };

            console.log("Params being sent:", params); // Debug log

            const employees = await this.orm.call(
                'hr.employee',
                'get_employee_attendance_data',
                [params]
            );

            console.log("Received employees data:", employees); // Debug log

            if (Array.isArray(employees)) {
                this.state.employeeData = employees;
                if (employees.length === 0) {
                    this.notification.add(
                        'Không tìm thấy dữ liệu phù hợp với điều kiện lọc',
                        {
                            type: 'info',
                        }
                    );
                }
            } else {
                console.error("Received invalid employee data format:", employees);
                this.notification.add(
                    'Dữ liệu nhận được không đúng định dạng',
                    {
                        type: 'danger',
                    }
                );
            }
        } catch (error) {
            console.error("Error loading employee data:", error);
            this.notification.add(
                'Không thể tải dữ liệu nhân viên',
                {
                    type: 'danger',
                }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    onChangeDate(ev) {
        this.state.selectedDate = ev.target.value;
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

    onChangeStatus(ev) {
        // Lấy tất cả các checkbox đã chọn
        const checkboxes = document.querySelectorAll('.status-checkboxes input[type="checkbox"]:checked');
        this.state.selectedStatus = Array.from(checkboxes).map(checkbox => checkbox.value);
    }

    async onViewReport() {
        // Cập nhật searchQuery từ input
        this.state.searchQuery = document.getElementById('search-bar').value;
        
        // Thêm thông báo loading
        this.notification.add(
            'Đang tải dữ liệu báo cáo...',
            {
                type: 'info',
            }
        );

        // Tải dữ liệu báo cáo
        await this.loadEmployeeData();
    }

    async _OnClickExcelReport() {
        if (this.state.isLoading) return;

        this.state.isLoading = true;
        try {
            const params = {
                selected_date: this.state.selectedDate,
                department_ids: this.state.selectedDepartments.length > 0 ? this.state.selectedDepartments : false, // Thay đổi thành department_ids
                search_query: document.getElementById('search-bar').value,
                status: this.state.selectedStatus,
            };
            
            const action = await this.orm.call(
                'hr.employee',
                'export_attendance_daily_excel',
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
}

AttendanceReportDaily.template = 'AttendanceReportDaily';

registry.category('actions').add('attendance_report_daily', AttendanceReportDaily);

export default AttendanceReportDaily;