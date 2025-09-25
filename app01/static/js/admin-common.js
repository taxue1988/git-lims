/**
 * 管理后台通用JavaScript函数库
 * 提供各种模块共用的功能
 */

// 全局变量
window.AdminCommon = {
    // CSRF令牌获取
    getCSRFToken: function() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    // 显示提示信息
    showAlert: function(message, type = 'info') {
        const alertClass = `alert-${type}`;
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.main-content').prepend(alertHtml);
        
        setTimeout(function() {
            $('.alert').fadeOut();
        }, 3000);
    },

    // 显示操作结果模态框
    showOperationResult: function(type, message) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
        
        $('#operation-result-content').html(`
            <div class="alert ${alertClass} mb-0">
                <i class="${iconClass} me-2"></i>
                ${message}
            </div>
        `);
        
        const modal = new bootstrap.Modal(document.getElementById('operation-result-modal'));
        modal.show();
    },

    // 通用分页渲染
    renderPagination: function(data, pageCallback) {
        if (data.total_pages <= 1) {
            $('#pagination-nav').hide();
            return;
        }
        
        let html = '';
        
        // 上一页
        if (data.has_previous) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="${pageCallback}(${data.current_page - 1})">&laquo;</a></li>`;
        } else {
            html += `<li class="page-item disabled"><span class="page-link">&laquo;</span></li>`;
        }
        
        // 页码
        for (let i = 1; i <= data.total_pages; i++) {
            if (i === data.current_page) {
                html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                html += `<li class="page-item"><a class="page-link" href="#" onclick="${pageCallback}(${i})">${i}</a></li>`;
            }
        }
        
        // 下一页
        if (data.has_next) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="${pageCallback}(${data.current_page + 1})">&raquo;</a></li>`;
        } else {
            html += `<li class="page-item disabled"><span class="page-link">&raquo;</span></li>`;
        }
        
        $('#pagination-ul').html(html);
        $('#pagination-nav').show();
    },

    // 通用AJAX请求
    ajaxRequest: function(url, method, data, successCallback, errorCallback) {
        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            },
            data: JSON.stringify(data),
            success: successCallback,
            error: errorCallback
        });
    },

    // 通用GET请求
    getRequest: function(url, params, successCallback, errorCallback) {
        $.ajax({
            url: url,
            method: 'GET',
            data: params,
            dataType: 'json',
            success: successCallback,
            error: errorCallback
        });
    },

    // 格式化日期
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    },

    // 获取状态对应的CSS类
    getStatusClass: function(status, statusMap) {
        return statusMap[status] || 'bg-secondary';
    },

    // 获取状态名称
    getStatusName: function(status, statusNameMap) {
        return statusNameMap[status] || '未知';
    },

    // 确认对话框
    confirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // 加载状态管理
    showLoading: function(button, text = '加载中...') {
        button.prop('disabled', true).html(`<i class="fas fa-spinner fa-spin"></i> ${text}`);
    },

    hideLoading: function(button, originalText) {
        button.prop('disabled', false).html(originalText);
    },

    // 表单验证
    validateForm: function(formSelector, rules) {
        const form = $(formSelector);
        let isValid = true;
        
        for (const field in rules) {
            const value = form.find(`[name="${field}"]`).val();
            const rule = rules[field];
            
            if (rule.required && !value) {
                this.showAlert(`${rule.label}不能为空`, 'danger');
                isValid = false;
                break;
            }
            
            if (rule.pattern && !rule.pattern.test(value)) {
                this.showAlert(rule.message || `${rule.label}格式不正确`, 'danger');
                isValid = false;
                break;
            }
        }
        
        return isValid;
    },

    // 表格操作按钮生成
    generateActionButtons: function(actions) {
        let html = '<div class="btn-group btn-group-sm" role="group">';
        
        actions.forEach(action => {
            const btnClass = action.class || 'btn-outline-primary';
            const icon = action.icon || 'fas fa-cog';
            const title = action.title || '';
            
            html += `
                <button type="button" class="btn ${btnClass} btn-sm" 
                        onclick="${action.onclick}" title="${title}">
                    <i class="${icon}"></i>
                </button>
            `;
        });
        
        html += '</div>';
        return html;
    }
};

// 页面加载完成后的通用初始化
$(document).ready(function() {
    // 绑定全选/取消全选功能
    $(document).on('change', '[id^="select-all"]', function() {
        const checkboxClass = $(this).attr('id').replace('select-all', '');
        const checkboxes = $(`.${checkboxClass}-checkbox`);
        checkboxes.prop('checked', this.checked);
    });

    // 绑定回车搜索
    $(document).on('keypress', '[id$="-search-input"]', function(e) {
        if (e.which === 13) {
            const searchCallback = $(this).data('search-callback');
            if (searchCallback && typeof window[searchCallback] === 'function') {
                window[searchCallback]();
            }
        }
    });

    // 绑定筛选变化事件
    $(document).on('change', '[id$="-filter"]', function() {
        const filterCallback = $(this).data('filter-callback');
        if (filterCallback && typeof window[filterCallback] === 'function') {
            window[filterCallback]();
        }
    });
});
