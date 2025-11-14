from django.contrib import admin
from django.urls import path
from app01 import views

urlpatterns = [
    # ==================== 管理后台页面（自定义） - 必须在 admin.site.urls 之前 ====================
    path('admin/experiment-tasks/', views.admin_experiment_tasks, name='admin_experiment_tasks'),
    path('admin/user-management/', views.admin_user_management, name='admin_user_management'),
    path('admin/overview/', views.admin_overview, name='admin_overview'),
    path('admin/station-management/manual/', views.admin_station_manual, name='admin_station_manual'),
    path('admin/station-management/reaction/', views.admin_station_reaction, name='admin_station_reaction'),
    path('admin/station-management/glove-reaction/', views.admin_station_glove_reaction, name='admin_station_glove_reaction'),
    path('admin/station-management/filtration/', views.admin_station_filtration, name='admin_station_filtration'),
    path('admin/station-management/rotavap/', views.admin_station_rotavap, name='admin_station_rotavap'),
    path('admin/station-management/column/', views.admin_station_column, name='admin_station_column'),
    path('admin/station-management/tlc/', views.admin_station_tlc, name='admin_station_tlc'),
    path('admin/station-management/gcms/', views.admin_station_gcms, name='admin_station_gcms'),
    path('admin/station-management/hplc/', views.admin_station_hplc, name='admin_station_hplc'),
    path('admin/station-management/agv/', views.admin_station_agv, name='admin_station_agv'),
    path('admin/station-management/batching/', views.admin_station_batching, name='admin_station_batching'),
    path('admin/test-ctrl/', views.admin_test_ctrl, name='admin_test_ctrl'),

    # ==================== Django Admin ====================
    path('admin/', admin.site.urls),

    # ==================== 认证与仪表板（页面） ====================
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user/task_management', views.user_task_management, name='user_task_management'),
    path('task/edit/', views.task_edit, name='task_edit'),

    # ==================== 用户任务 API（用户端） ====================
    path('api/user/task/create/', views.api_user_task_create, name='api_user_task_create'),
    path('api/user/tasks/', views.api_user_tasks, name='api_user_tasks'),
    path('api/user/task/<int:task_id>/', views.api_user_task_detail, name='api_user_task_detail'),
    path('api/user/task/<int:task_id>/update/', views.api_user_task_update, name='api_user_task_update'),
    path('api/user/task/<int:task_id>/delete/', views.api_delete_task, name='api_delete_task'),
    path('api/user/task/<int:task_id>/submit/', views.api_submit_task, name='api_submit_task'),
    path('api/user/task/<int:task_id>/result/', views.api_task_result, name='api_task_result'),
    path('api/user/task/<int:task_id>/copy/', views.api_user_task_copy, name='api_user_task_copy'),

    # ==================== 任务管理 API（管理员）与公共接口 ====================
    path('api/tasks/submit/', views.api_submit_tasks, name='api_submit_tasks'),
    path('api/filter-tasks/', views.api_filter_tasks, name='api_filter_tasks'),
    path('api/task/<int:task_id>/', views.api_task_detail, name='api_task_detail'),
    path('api/batch-update-tasks/', views.api_batch_update_tasks, name='api_batch_update_tasks'),
    path('api/task/<int:task_id>/update/', views.api_single_update_task, name='api_single_update_task'),

    # ==================== 用户管理 API ====================
    path('api/users/', views.api_users_list, name='api_users_list'),
    path('api/user/create/', views.api_user_create, name='api_user_create'),
    path('api/user/<int:user_id>/', views.api_user_detail, name='api_user_detail'),
    path('api/user/<int:user_id>/update/', views.api_user_update, name='api_user_update'),
    path('api/user/<int:user_id>/delete/', views.api_user_delete, name='api_user_delete'),
    path('api/user/<int:user_id>/toggle-status/', views.api_user_toggle_status, name='api_user_toggle_status'),
    path('api/user/<int:user_id>/reset-password/', views.api_user_reset_password, name='api_user_reset_password'),
    path('api/user/statistics/', views.api_user_statistics, name='api_user_statistics'),

    # ==================== 数据建模分析功能路由 ====================
    
    # 数据建模分析页面路由
    path('user/analysis_train/', views.user_analysis_train, name='user_analysis_train'),
    path('ml/data-analysis/', views.ml_data_analysis, name='ml_data_analysis'),
    path('ml/model-creation/', views.ml_model_creation, name='ml_model_creation'),
    path('ml/task-management/', views.ml_task_management, name='ml_task_management'),
    path('ml/task/<int:task_id>/', views.ml_task_detail, name='ml_task_detail'),

    # ==================== 贝叶斯优化页面（用户） ====================
    path('bo/home/', views.bo_home, name='bo_home'),
    path('bo/tasks/', views.bo_task_center, name='bo_task_center'),

    # ==================== 机器学习API路由 ====================
    
    # 数据文件管理API
    path('api/ml/data-files/', views.api_ml_data_files_list, name='api_ml_data_files_list'),
    path('api/ml/data-files/upload/', views.api_ml_data_files_upload, name='api_ml_data_files_upload'),
    path('api/ml/data-files/<int:file_id>/', views.api_ml_data_files_detail, name='api_ml_data_files_detail'),
    path('api/ml/data-files/<int:file_id>/download/', views.api_ml_data_files_download, name='api_ml_data_files_download'),
    path('api/ml/data-files/<int:file_id>/preview/', views.api_ml_data_files_preview, name='api_ml_data_files_preview'),
    path('api/ml/data-files/<int:file_id>/process/', views.api_ml_data_files_process, name='api_ml_data_files_process'),
    path('api/ml/data-files/<int:file_id>/delete/', views.api_ml_data_files_delete, name='api_ml_data_files_delete'),
    
    # 数据处理API
    path('api/ml/data-processing/missing-values/', views.api_ml_missing_values_analysis, name='api_ml_missing_values_analysis'),
    path('api/ml/data-processing/outliers/', views.api_ml_outliers_analysis, name='api_ml_outliers_analysis'),
    path('api/ml/data-processing/split/', views.api_ml_data_split, name='api_ml_data_split'),
    
    # 机器学习算法API
    path('api/ml/algorithms/', views.api_ml_algorithms_list, name='api_ml_algorithms_list'),
    path('api/ml/algorithms/<int:algorithm_id>/parameters/', views.api_ml_algorithms_parameters, name='api_ml_algorithms_parameters'),
    
    # 机器学习任务API
    path('api/ml/tasks/', views.api_ml_tasks_list, name='api_ml_tasks_list'),
    path('api/ml/tasks/create/', views.api_ml_tasks_create, name='api_ml_tasks_create'),
    path('api/ml/tasks/<int:task_id>/', views.api_ml_tasks_detail, name='api_ml_tasks_detail'),
    path('api/ml/tasks/<int:task_id>/start/', views.api_ml_tasks_start, name='api_ml_tasks_start'),
    path('api/ml/tasks/<int:task_id>/stop/', views.api_ml_tasks_stop, name='api_ml_tasks_stop'),
    path('api/ml/tasks/<int:task_id>/delete/', views.api_ml_tasks_delete, name='api_ml_tasks_delete'),
    path('api/ml/tasks/<int:task_id>/result/', views.api_ml_tasks_result, name='api_ml_tasks_result'),
    path('api/ml/tasks/<int:task_id>/progress/', views.api_ml_tasks_progress, name='api_ml_tasks_progress'),

    # ==================== 贝叶斯优化 API ====================
    path('api/bo/tasks/', views.api_bo_tasks_list, name='api_bo_tasks_list'),
    path('api/bo/tasks/create/', views.api_bo_tasks_create, name='api_bo_tasks_create'),
    path('api/bo/tasks/<int:bo_task_id>/', views.api_bo_tasks_detail, name='api_bo_tasks_detail'),
    path('api/bo/tasks/<int:bo_task_id>/delete/', views.api_bo_tasks_delete, name='api_bo_tasks_delete'),
    path('api/bo/tasks/<int:bo_task_id>/set-params/', views.api_bo_set_parameter_space, name='api_bo_set_parameter_space'),
    path('api/bo/tasks/<int:bo_task_id>/upload-csv/', views.api_bo_upload_csv, name='api_bo_upload_csv'),
    path('api/bo/tasks/<int:bo_task_id>/upsert-history/', views.api_bo_upsert_history, name='api_bo_upsert_history'),
    path('api/bo/tasks/<int:bo_task_id>/history/', views.api_bo_history, name='api_bo_history'),
    path('api/bo/tasks/<int:bo_task_id>/start-iteration/', views.api_bo_start_iteration, name='api_bo_start_iteration'),
    path('api/bo/iterations/<int:iteration_id>/submit-observation/', views.api_bo_submit_observation, name='api_bo_submit_observation'),
    path('api/bo/iterations/<int:iteration_id>/download/', views.api_bo_download_iteration, name='api_bo_download_iteration'),
    path('api/bo/tasks/<int:bo_task_id>/download-all/', views.api_bo_download_all, name='api_bo_download_all'),

    # ==================== 备料员页面 ====================
    path('preparator/tasks/', views.preparator_tasks, name='preparator_tasks'),
    path('preparator/fill_container/', views.fill_container, name='preparator_fill_container'),
    path('preparator/container_management/', views.preparator_container_management, name='preparator_container_management'),
    path('preparator/material_management/', views.preparator_material_management, name='preparator_material_management'),
    path('preparator/preparation_station/', views.preparation_station_view, name='preparation_station'),
    path('preparator/reagents_library/', views.preparator_reagents_library, name='preparator_reagents_library'),

    # ==================== 试剂库 API ====================
    path('api/reagents/stats/', views.api_reagents_stats, name='api_reagents_stats'),
    path('api/reagents/', views.api_reagents_list, name='api_reagents_list'),
    path('api/reagent/create/', views.api_reagent_create, name='api_reagent_create'),
    path('api/reagent/<int:reagent_id>/', views.api_reagent_detail, name='api_reagent_detail'),
    path('api/reagent/<int:reagent_id>/update/', views.api_reagent_update, name='api_reagent_update'),
    path('api/reagent/<int:reagent_id>/delete/', views.api_reagent_delete, name='api_reagent_delete'),
    path('api/reagent/<int:reagent_id>/take/', views.api_reagent_take, name='api_reagent_take'),
    # 图谱
    path('api/reagent/<int:reagent_id>/spectra/', views.api_reagent_spectra, name='api_reagent_spectra'),
    path('api/reagent/<int:reagent_id>/spectra/upload/', views.api_reagent_spectrum_upload, name='api_reagent_spectrum_upload'),
    path('api/reagent/spectra/<int:spectrum_id>/update/', views.api_reagent_spectrum_update, name='api_reagent_spectrum_update'),
    path('api/reagent/spectra/<int:spectrum_id>/delete/', views.api_reagent_spectrum_delete, name='api_reagent_spectrum_delete'),
    path('api/reagent/spectra/<int:spectrum_id>/download/', views.api_reagent_spectrum_download, name='api_reagent_spectrum_download'),

    # ==================== 备料员任务 API ====================
    path('api/preparator/filter-tasks/', views.api_preparator_filter_tasks, name='api_preparator_filter_tasks'),
    path('api/preparator/task/<int:task_id>/', views.api_preparator_task_detail, name='api_preparator_task_detail'),
    path('api/preparator/batch-prepare/', views.api_preparator_batch_prepare, name='api_preparator_batch_prepare'),

    # ==================== 备料工站 API ====================
    path('api/preparation-station/place-container/', views.place_container, name='place_container'),
    path('api/preparation-station/remove-container/', views.remove_container, name='remove_container'),
    path('api/preparation-station/available-containers/', views.get_available_containers, name='get_available_containers'),
    path('api/preparation-station/free-positions/', views.api_free_preparation_positions, name='api_free_preparation_positions'),
    path('api/preparation-station/occupied-containers/', views.api_occupied_preparation_containers, name='api_occupied_preparation_containers'),
    
    # ==================== 固液配料工站 API ====================
    path('api/batching-station/place-container/', views.api_batching_station_place_container, name='api_batching_station_place_container'),

    # ==================== 转移仓 API ====================
    # 规格/列表/统计
    path('api/containers/specs/', views.api_container_specs, name='api_container_specs'),
    path('api/containers/', views.api_containers, name='api_containers'),
    path('api/containers/stats/', views.api_containers_stats, name='api_containers_stats'),
    path('api/containers/names/', views.api_containers_names, name='api_containers_names'),
    # 创建/详情/操作
    path('api/containers/create/', views.api_container_create, name='api_container_create'),
    path('api/containers/<int:container_id>/', views.api_container_detail, name='api_container_detail'),
    path('api/containers/<int:container_id>/fill-slot/', views.api_container_fill_slot, name='api_container_fill_slot'),
    path('api/containers/<int:container_id>/complete/', views.api_container_complete, name='api_container_complete'),
    path('api/containers/<int:container_id>/clear/', views.api_container_clear, name='api_container_clear'),
    path('api/containers/<int:container_id>/delete/', views.api_container_delete, name='api_container_delete'),
    # 导出
    path('api/containers/export/names/', views.api_containers_export_names, name='api_containers_export_names'),

    # ==================== 备料清单 API ====================
    path('api/preparation-lists/', views.api_preparation_lists, name='api_preparation_lists'),
    path('api/preparation-list/<str:preparation_id>/', views.api_preparation_list_detail, name='api_preparation_list_detail'),
    path('api/preparation-list/<str:preparation_id>/delete/', views.api_preparation_list_delete, name='api_preparation_list_delete'),

    # ==================== 物料 API ====================
    # 列表/统计/查询
    path('api/materials/', views.api_materials, name='api_materials'),
    path('api/materials/stats/', views.api_materials_stats, name='api_materials_stats'),
    path('api/materials/by-name/', views.api_material_by_name, name='api_material_by_name'),
    # 创建/详情/编辑/更新/清空/删除
    path('api/materials/create/', views.api_material_create, name='api_material_create'),
    path('api/materials/<str:kind>/<int:mat_id>/', views.api_material_detail, name='api_material_detail'),
    path('api/materials/<str:kind>/<int:mat_id>/edit/', views.api_material_edit, name='api_material_edit'),
    path('api/materials/<str:kind>/<int:mat_id>/update/', views.api_material_update, name='api_material_update'),
    path('api/materials/<str:kind>/<int:mat_id>/clear/', views.api_material_clear, name='api_material_clear'),
    path('api/materials/<str:kind>/<int:mat_id>/delete/', views.api_material_delete, name='api_material_delete'),
    # 导出
    path('api/materials/export/names/', views.api_materials_export_names, name='api_materials_export_names'),
]