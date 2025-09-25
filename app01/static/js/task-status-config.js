/**
 * 任务状态配置管理
 * 统一管理前端状态显示、样式和转换规则
 */

// 任务状态配置
const TASK_STATUS_CONFIG = {
    draft: {
        label: '草稿',
        class: 'bg-secondary',
        icon: 'fa-edit',
        color: '#6c757d',
        description: '任务已创建但未提交'
    },
    pending: {
        label: '待审核',
        class: 'bg-info',
        icon: 'fa-hourglass-half',
        color: '#17a2b8',
        description: '任务已提交，等待管理员审核'
    },
    approved: {
        label: '已通过',
        class: 'bg-primary',
        icon: 'fa-check',
        color: '#007bff',
        description: '任务已通过审核'
    },
    scheduled: {
        label: '已排程',
        class: 'bg-warning',
        icon: 'fa-calendar',
        color: '#ffc107',
        description: '任务已安排执行时间'
    },
    in_progress: {
        label: '进行中',
        class: 'bg-warning',
        icon: 'fa-spinner fa-spin',
        color: '#ffc107',
        description: '任务正在执行中'
    },
    completed: {
        label: '已完成',
        class: 'bg-success',
        icon: 'fa-check-circle',
        color: '#28a745',
        description: '任务已完成'
    },
    rejected: {
        label: '已驳回',
        class: 'bg-danger',
        icon: 'fa-times',
        color: '#dc3545',
        description: '任务被驳回，需要修改后重新提交'
    },
    cancelled: {
        label: '已取消',
        class: 'bg-secondary',
        icon: 'fa-ban',
        color: '#6c757d',
        description: '任务已被取消'
    }
};

// 状态转换规则
const STATUS_TRANSITIONS = {
    draft: ['pending'],
    pending: ['approved', 'rejected'],
    approved: ['scheduled'],
    scheduled: ['in_progress', 'cancelled'],
    in_progress: ['completed', 'cancelled'],
    completed: [],
    rejected: ['pending'],
    cancelled: []
};

// 状态映射（中文到英文）
const STATUS_MAPPING = {
    '草稿': 'draft',
    '待审核': 'pending',
    '已通过': 'approved',
    '已排程': 'scheduled',
    '进行中': 'in_progress',
    '已完成': 'completed',
    '已驳回': 'rejected',
    '已取消': 'cancelled'
};

// 反向状态映射（英文到中文）
const REVERSE_STATUS_MAPPING = {
    'draft': '草稿',
    'pending': '待审核',
    'approved': '已通过',
    'scheduled': '已排程',
    'in_progress': '进行中',
    'completed': '已完成',
    'rejected': '已驳回',
    'cancelled': '已取消'
};

/**
 * 任务状态管理类
 */
class TaskStatusManager {
    /**
     * 获取状态配置
     * @param {string} status 状态值
     * @returns {object} 状态配置对象
     */
    static getStatusConfig(status) {
        return TASK_STATUS_CONFIG[status] || TASK_STATUS_CONFIG.draft;
    }

    /**
     * 获取状态显示名称
     * @param {string} status 状态值
     * @returns {string} 状态显示名称
     */
    static getStatusLabel(status) {
        const config = this.getStatusConfig(status);
        return config.label;
    }

    /**
     * 获取状态CSS类
     * @param {string} status 状态值
     * @returns {string} CSS类名
     */
    static getStatusClass(status) {
        const config = this.getStatusConfig(status);
        return config.class;
    }

    /**
     * 获取状态图标
     * @param {string} status 状态值
     * @returns {string} 图标类名
     */
    static getStatusIcon(status) {
        const config = this.getStatusConfig(status);
        return config.icon;
    }

    /**
     * 获取状态颜色
     * @param {string} status 状态值
     * @returns {string} 颜色值
     */
    static getStatusColor(status) {
        const config = this.getStatusConfig(status);
        return config.color;
    }

    /**
     * 获取状态描述
     * @param {string} status 状态值
     * @returns {string} 状态描述
     */
    static getStatusDescription(status) {
        const config = this.getStatusConfig(status);
        return config.description;
    }

    /**
     * 检查状态转换是否合法
     * @param {string} fromStatus 原状态
     * @param {string} toStatus 目标状态
     * @returns {boolean} 是否可以转换
     */
    static canTransition(fromStatus, toStatus) {
        const availableTransitions = STATUS_TRANSITIONS[fromStatus] || [];
        return availableTransitions.includes(toStatus);
    }

    /**
     * 获取可用的状态转换选项
     * @param {string} currentStatus 当前状态
     * @returns {array} 可用的转换选项
     */
    static getAvailableTransitions(currentStatus) {
        return STATUS_TRANSITIONS[currentStatus] || [];
    }

    /**
     * 将中文状态转换为英文状态
     * @param {string} chineseStatus 中文状态
     * @returns {string} 英文状态
     */
    static chineseToEnglish(chineseStatus) {
        return STATUS_MAPPING[chineseStatus] || 'draft';
    }

    /**
     * 将英文状态转换为中文状态
     * @param {string} englishStatus 英文状态
     * @returns {string} 中文状态
     */
    static englishToChinese(englishStatus) {
        return REVERSE_STATUS_MAPPING[englishStatus] || '草稿';
    }

    /**
     * 检查任务是否可编辑
     * @param {string} status 状态值
     * @returns {boolean} 是否可编辑
     */
    static isEditable(status) {
        return ['draft', 'rejected'].includes(status);
    }

    /**
     * 检查任务是否可删除
     * @param {string} status 状态值
     * @returns {boolean} 是否可删除
     */
    static isDeletable(status) {
        return ['draft', 'rejected'].includes(status);
    }

    /**
     * 检查任务是否可提交
     * @param {string} status 状态值
     * @returns {boolean} 是否可提交
     */
    static isSubmittable(status) {
        return ['draft', 'rejected'].includes(status);
    }

    /**
     * 渲染状态徽章
     * @param {string} status 状态值
     * @param {string} size 徽章大小 ('sm', 'md', 'lg')
     * @returns {string} HTML字符串
     */
    static renderStatusBadge(status, size = 'md') {
        const config = this.getStatusConfig(status);
        const sizeClass = size === 'sm' ? 'badge-sm' : size === 'lg' ? 'badge-lg' : '';
        return `<span class="badge ${config.class} ${sizeClass}" title="${config.description}">
            <i class="fas ${config.icon} me-1"></i>${config.label}
        </span>`;
    }

    /**
     * 渲染状态选择器
     * @param {string} currentStatus 当前状态
     * @param {string} name 选择器名称
     * @param {string} id 选择器ID
     * @returns {string} HTML字符串
     */
    static renderStatusSelector(currentStatus, name = 'status', id = 'status-selector') {
        const availableTransitions = this.getAvailableTransitions(currentStatus);
        let html = `<select class="form-select" name="${name}" id="${id}">`;
        
        availableTransitions.forEach(status => {
            const config = this.getStatusConfig(status);
            const selected = status === currentStatus ? 'selected' : '';
            html += `<option value="${status}" ${selected}>${config.label}</option>`;
        });
        
        html += '</select>';
        return html;
    }
}

// 导出到全局作用域
window.TaskStatusManager = TaskStatusManager;
window.TASK_STATUS_CONFIG = TASK_STATUS_CONFIG;
window.STATUS_TRANSITIONS = STATUS_TRANSITIONS;
window.STATUS_MAPPING = STATUS_MAPPING;
window.REVERSE_STATUS_MAPPING = REVERSE_STATUS_MAPPING;
