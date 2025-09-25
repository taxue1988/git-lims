/**
 * 用户界面通用JavaScript函数
 * 提供各种常用的工具函数和功能
 */

// 全局变量
const USER_COMMON = {
    // 配置
    config: {
        toastDuration: 3000,
        animationDuration: 300,
        apiTimeout: 10000
    },
    
    // 状态
    state: {
        isLoading: false,
        currentPage: 'dashboard'
    }
};

/**
 * 通用工具函数
 */
const Utils = {
    /**
     * 防抖函数
     * @param {Function} func 要执行的函数
     * @param {number} wait 等待时间
     * @param {boolean} immediate 是否立即执行
     */
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    /**
     * 节流函数
     * @param {Function} func 要执行的函数
     * @param {number} limit 限制时间
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 格式化日期
     * @param {Date|string} date 日期对象或日期字符串
     * @param {string} format 格式字符串
     */
    formatDate: function(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },

    /**
     * 格式化文件大小
     * @param {number} bytes 字节数
     * @param {number} decimals 小数位数
     */
    formatFileSize: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    /**
     * 生成随机ID
     * @param {number} length ID长度
     */
    generateId: function(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * 深拷贝对象
     * @param {*} obj 要拷贝的对象
     */
    deepClone: function(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * 验证邮箱格式
     * @param {string} email 邮箱地址
     */
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * 验证手机号格式
     * @param {string} phone 手机号
     */
    isValidPhone: function(phone) {
        const phoneRegex = /^1[3-9]\d{9}$/;
        return phoneRegex.test(phone);
    }
};

/**
 * 本地存储管理
 */
const Storage = {
    /**
     * 设置本地存储
     * @param {string} key 键名
     * @param {*} value 值
     * @param {number} expire 过期时间（秒）
     */
    set: function(key, value, expire = null) {
        const data = {
            value: value,
            timestamp: Date.now()
        };
        
        if (expire) {
            data.expire = expire * 1000;
        }
        
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('存储数据失败:', e);
            return false;
        }
    },

    /**
     * 获取本地存储
     * @param {string} key 键名
     * @param {*} defaultValue 默认值
     */
    get: function(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(key);
            if (!data) return defaultValue;
            
            const parsed = JSON.parse(data);
            
            // 检查是否过期
            if (parsed.expire && (Date.now() - parsed.timestamp) > parsed.expire) {
                localStorage.removeItem(key);
                return defaultValue;
            }
            
            return parsed.value;
        } catch (e) {
            console.error('读取数据失败:', e);
            return defaultValue;
        }
    },

    /**
     * 删除本地存储
     * @param {string} key 键名
     */
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('删除数据失败:', e);
            return false;
        }
    },

    /**
     * 清空所有本地存储
     */
    clear: function() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('清空数据失败:', e);
            return false;
        }
    },

    /**
     * 获取所有键名
     */
    keys: function() {
        try {
            return Object.keys(localStorage);
        } catch (e) {
            console.error('获取键名失败:', e);
            return [];
        }
    }
};

/**
 * 网络请求管理
 */
const Network = {
    /**
     * 发送GET请求
     * @param {string} url 请求URL
     * @param {Object} options 请求选项
     */
    get: function(url, options = {}) {
        return this.request(url, 'GET', null, options);
    },

    /**
     * 发送POST请求
     * @param {string} url 请求URL
     * @param {Object} data 请求数据
     * @param {Object} options 请求选项
     */
    post: function(url, data = null, options = {}) {
        return this.request(url, 'POST', data, options);
    },

    /**
     * 发送PUT请求
     * @param {string} url 请求URL
     * @param {Object} data 请求数据
     * @param {Object} options 请求选项
     */
    put: function(url, data = null, options = {}) {
        return this.request(url, 'PUT', data, options);
    },

    /**
     * 发送DELETE请求
     * @param {string} url 请求URL
     * @param {Object} options 请求选项
     */
    delete: function(url, options = {}) {
        return this.request(url, 'DELETE', null, options);
    },

    /**
     * 通用请求函数
     * @param {string} url 请求URL
     * @param {string} method 请求方法
     * @param {Object} data 请求数据
     * @param {Object} options 请求选项
     */
    request: function(url, method, data = null, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: USER_COMMON.config.apiTimeout
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        if (data && method !== 'GET') {
            finalOptions.body = JSON.stringify(data);
        }

        // 添加CSRF令牌
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            finalOptions.headers['X-CSRFToken'] = csrfToken;
        }

        return fetch(url, {
            method: method,
            headers: finalOptions.headers,
            body: finalOptions.body,
            signal: AbortSignal.timeout(finalOptions.timeout)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('请求失败:', error);
            throw error;
        });
    },

    /**
     * 获取CSRF令牌
     */
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
    }
};

/**
 * 任务服务：统一封装任务相关API调用（仅用于任务域，禁止再使用本地存储持久化任务）
 */
const TaskService = {
    list: function(params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = '/api/user/tasks/' + (query ? ('?' + query) : '');
        return Network.get(url);
    },
    detail: function(id) {
        return Network.get(`/api/user/task/${id}/`);
    },
    create: function(payload) {
        return Network.post('/api/user/task/create/', payload);
    },
    update: function(id, payload) {
        return Network.put(`/api/user/task/${id}/update/`, payload);
    },
    submit: function(id) {
        return Network.post(`/api/user/task/${id}/submit/`);
    },
    remove: function(id) {
        return Network.delete(`/api/user/task/${id}/delete/`);
    },
    submitBatchFromLocal: function(items) {
        // 迁移期：用于一次性导入本地遗留任务
        return Network.post('/api/tasks/submit/', { tasks: items });
    }
};

/**
 * 表单验证
 */
const Validation = {
    /**
     * 验证必填字段
     * @param {string} value 字段值
     * @param {string} fieldName 字段名称
     */
    required: function(value, fieldName = '字段') {
        if (!value || value.trim() === '') {
            return `${fieldName}不能为空`;
        }
        return null;
    },

    /**
     * 验证最小长度
     * @param {string} value 字段值
     * @param {number} minLength 最小长度
     * @param {string} fieldName 字段名称
     */
    minLength: function(value, minLength, fieldName = '字段') {
        if (value && value.length < minLength) {
            return `${fieldName}长度不能少于${minLength}个字符`;
        }
        return null;
    },

    /**
     * 验证最大长度
     * @param {string} value 字段值
     * @param {number} maxLength 最大长度
     * @param {string} fieldName 字段名称
     */
    maxLength: function(value, maxLength, fieldName = '字段') {
        if (value && value.length > maxLength) {
            return `${fieldName}长度不能超过${maxLength}个字符`;
        }
        return null;
    },

    /**
     * 验证邮箱格式
     * @param {string} value 邮箱值
     * @param {string} fieldName 字段名称
     */
    email: function(value, fieldName = '邮箱') {
        if (value && !Utils.isValidEmail(value)) {
            return `${fieldName}格式不正确`;
        }
        return null;
    },

    /**
     * 验证手机号格式
     * @param {string} value 手机号值
     * @param {string} fieldName 字段名称
     */
    phone: function(value, fieldName = '手机号') {
        if (value && !Utils.isValidPhone(value)) {
            return `${fieldName}格式不正确`;
        }
        return null;
    },

    /**
     * 验证数字范围
     * @param {number} value 数值
     * @param {number} min 最小值
     * @param {number} max 最大值
     * @param {string} fieldName 字段名称
     */
    numberRange: function(value, min, max, fieldName = '字段') {
        if (value !== null && value !== undefined) {
            const num = parseFloat(value);
            if (isNaN(num)) {
                return `${fieldName}必须是数字`;
            }
            if (num < min || num > max) {
                return `${fieldName}必须在${min}到${max}之间`;
            }
        }
        return null;
    },

    /**
     * 验证表单
     * @param {Object} formData 表单数据
     * @param {Object} rules 验证规则
     */
    validateForm: function(formData, rules) {
        const errors = {};
        
        for (const field in rules) {
            const fieldRules = rules[field];
            const value = formData[field];
            
            for (const rule of fieldRules) {
                let error = null;
                
                switch (rule.type) {
                    case 'required':
                        error = this.required(value, rule.message || field);
                        break;
                    case 'minLength':
                        error = this.minLength(value, rule.value, rule.message || field);
                        break;
                    case 'maxLength':
                        error = this.maxLength(value, rule.value, rule.message || field);
                        break;
                    case 'email':
                        error = this.email(value, rule.message || field);
                        break;
                    case 'phone':
                        error = this.phone(value, rule.message || field);
                        break;
                    case 'numberRange':
                        error = this.numberRange(value, rule.min, rule.max, rule.message || field);
                        break;
                    case 'custom':
                        if (rule.validator) {
                            error = rule.validator(value, formData);
                        }
                        break;
                }
                
                if (error) {
                    errors[field] = error;
                    break; // 一个字段只显示第一个错误
                }
            }
        }
        
        return {
            isValid: Object.keys(errors).length === 0,
            errors: errors
        };
    }
};

/**
 * 页面导航管理
 */
const Navigation = {
    /**
     * 导航到指定页面
     * @param {string} url 目标URL
     * @param {Object} options 导航选项
     */
    navigate: function(url, options = {}) {
        const defaultOptions = {
            replace: false,
            newTab: false
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        if (finalOptions.newTab) {
            window.open(url, '_blank');
        } else if (finalOptions.replace) {
            window.location.replace(url);
        } else {
            window.location.href = url;
        }
    },

    /**
     * 返回上一页
     */
    goBack: function() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            this.navigate('/');
        }
    },

    /**
     * 刷新当前页面
     */
    refresh: function() {
        window.location.reload();
    },

    /**
     * 获取当前页面URL参数
     * @param {string} name 参数名
     */
    getUrlParam: function(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },

    /**
     * 设置页面标题
     * @param {string} title 标题
     */
    setTitle: function(title) {
        document.title = title;
    }
};

/**
 * 数据导出功能
 */
const Export = {
    /**
     * 导出为CSV
     * @param {Array} data 数据数组
     * @param {Array} headers 表头
     * @param {string} filename 文件名
     */
    toCSV: function(data, headers, filename = 'export.csv') {
        if (!data || data.length === 0) {
            console.warn('没有数据可导出');
            return;
        }

        let csvContent = '';
        
        // 添加表头
        if (headers && headers.length > 0) {
            csvContent += headers.join(',') + '\n';
        }
        
        // 添加数据行
        data.forEach(row => {
            const values = Object.values(row).map(value => {
                // 处理包含逗号、引号或换行符的值
                if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            });
            csvContent += values.join(',') + '\n';
        });
        
        this.downloadFile(csvContent, filename, 'text/csv');
    },

    /**
     * 导出为JSON
     * @param {Object|Array} data 数据
     * @param {string} filename 文件名
     */
    toJSON: function(data, filename = 'export.json') {
        const jsonContent = JSON.stringify(data, null, 2);
        this.downloadFile(jsonContent, filename, 'application/json');
    },

    /**
     * 下载文件
     * @param {string} content 文件内容
     * @param {string} filename 文件名
     * @param {string} mimeType MIME类型
     */
    downloadFile: function(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    }
};

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化用户界面
    initUserInterface();
    
    // 绑定全局事件
    bindGlobalEvents();
});

/**
 * 初始化用户界面
 */
function initUserInterface() {
    console.log('初始化用户界面...');
    
    // 设置当前页面状态
    const currentPath = window.location.pathname;
    if (currentPath.includes('dashboard')) {
        USER_COMMON.state.currentPage = 'dashboard';
    } else if (currentPath.includes('analysis')) {
        USER_COMMON.state.currentPage = 'analysis';
    }
    
    // 高亮当前导航项
    highlightCurrentNavigation();
    
    // 初始化响应式侧边栏
    initResponsiveSidebar();
}

/**
 * 高亮当前导航项
 */
function highlightCurrentNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active', 'bg-primary', 'bg-success');
        
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            if (currentPath.includes('dashboard')) {
                link.classList.add('bg-primary');
            } else if (currentPath.includes('analysis')) {
                link.classList.add('bg-success');
            }
        }
    });
}

/**
 * 初始化响应式侧边栏
 */
function initResponsiveSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.navbar-toggler');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // 点击外部区域关闭侧边栏
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/**
 * 绑定全局事件
 */
function bindGlobalEvents() {
    // 窗口大小改变事件
    window.addEventListener('resize', Utils.debounce(function() {
        handleWindowResize();
    }, 250));
    
    // 页面可见性改变事件
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('页面隐藏');
        } else {
            console.log('页面显示');
        }
    });
}

/**
 * 处理窗口大小改变
 */
function handleWindowResize() {
    const width = window.innerWidth;
    const sidebar = document.querySelector('.sidebar');
    
    if (width <= 768 && sidebar) {
        sidebar.classList.remove('show');
    }
}

/**
 * 全局错误处理
 */
window.addEventListener('error', function(e) {
    console.error('全局错误:', e.error);
    showToast('发生错误，请刷新页面重试', 'danger');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('未处理的Promise拒绝:', e.reason);
    showToast('网络请求失败，请检查网络连接', 'danger');
});

// 导出到全局作用域
window.USER_COMMON = USER_COMMON;
window.Utils = Utils;
window.Storage = Storage;
window.Network = Network;
window.Validation = Validation;
window.Navigation = Navigation;
window.Export = Export;
