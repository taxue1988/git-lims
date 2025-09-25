from django.core.management.base import BaseCommand
from app01.models import MLAlgorithm


REGRESSION_ALGORITHMS = [
    {
        'name': 'linear_regression',
        'display_name': '线性最小二乘法（Linear Regression）',
        'algorithm_type': 'regression',
        'description': '最基础的线性回归，最小化残差平方和。',
        'default_parameters': {
            'fit_intercept': True,
            'positive': False
        },
        'parameter_schema': {
            'fit_intercept': { 'type': 'boolean', 'default': True, 'help': '是否拟合截距项。' },
            'positive': { 'type': 'boolean', 'default': False, 'help': '是否约束系数为非负。' }
        }
    },
    {
        'name': 'ridge',
        'display_name': '岭回归（Ridge）',
        'algorithm_type': 'regression',
        'description': 'L2 正则化，缓解多重共线性，提升泛化能力。',
        'default_parameters': {
            'alpha': 1.0,
            'fit_intercept': True,
            'solver': 'auto'
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1, 'help': 'L2 正则化强度。' },
            'fit_intercept': { 'type': 'boolean', 'default': True, 'help': '是否拟合截距。' },
            'solver': { 'type': 'select', 'default': 'auto', 'options': ['auto','svd','cholesky','lsqr','sparse_cg','sag','saga'], 'help': '求解器。' }
        }
    },
    {
        'name': 'lasso',
        'display_name': 'Lasso 回归（L1）',
        'algorithm_type': 'regression',
        'description': 'L1 正则化，可进行特征选择与稀疏化。',
        'default_parameters': {
            'alpha': 1.0,
            'fit_intercept': True,
            'max_iter': 1000
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1, 'help': 'L1 正则化强度。' },
            'fit_intercept': { 'type': 'boolean', 'default': True, 'help': '是否拟合截距。' },
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100, 'help': '最大迭代次数。' }
        }
    },
    {
        'name': 'bayesian_ridge',
        'display_name': '贝叶斯岭回归（Bayesian Ridge）',
        'algorithm_type': 'regression',
        'description': '贝叶斯框架下的岭回归，参数带有先验分布。',
        'default_parameters': {
            'n_iter': 300,
            'alpha_1': 1e-6,
            'alpha_2': 1e-6,
            'lambda_1': 1e-6,
            'lambda_2': 1e-6
        },
        'parameter_schema': {
            'n_iter': { 'type': 'number', 'default': 300, 'min': 100, 'step': 50, 'help': '迭代次数。' },
            'alpha_1': { 'type': 'number', 'default': 1e-6, 'step': 1e-6, 'help': 'alpha 先验 Gamma 分布参数。' },
            'alpha_2': { 'type': 'number', 'default': 1e-6, 'step': 1e-6, 'help': 'alpha 先验 Gamma 分布参数。' },
            'lambda_1': { 'type': 'number', 'default': 1e-6, 'step': 1e-6, 'help': 'lambda 先验 Gamma 分布参数。' },
            'lambda_2': { 'type': 'number', 'default': 1e-6, 'step': 1e-6, 'help': 'lambda 先验 Gamma 分布参数。' }
        }
    },
    {
        'name': 'ard',
        'display_name': 'ARD 回归',
        'algorithm_type': 'regression',
        'description': '自动相关性确定（Automatic Relevance Determination）。',
        'default_parameters': {
            'n_iter': 300,
            'tol': 1e-3,
            'alpha_1': 1e-6,
            'alpha_2': 1e-6,
            'lambda_1': 1e-6,
            'lambda_2': 1e-6
        },
        'parameter_schema': {
            'n_iter': { 'type': 'number', 'default': 300, 'min': 100, 'step': 50, 'help': '迭代次数。' },
            'tol': { 'type': 'number', 'default': 1e-3, 'step': 1e-4, 'help': '收敛容忍度。' },
            'alpha_1': { 'type': 'number', 'default': 1e-6, 'step': 1e-6 },
            'alpha_2': { 'type': 'number', 'default': 1e-6, 'step': 1e-6 },
            'lambda_1': { 'type': 'number', 'default': 1e-6, 'step': 1e-6 },
            'lambda_2': { 'type': 'number', 'default': 1e-6, 'step': 1e-6 }
        }
    },
    {
        'name': 'glm',
        'display_name': '广义线性回归（GLM）',
        'algorithm_type': 'regression',
        'description': '广义线性模型，支持不同分布与链接函数。',
        'default_parameters': {
            'family': 'gaussian',
            'link': 'identity'
        },
        'parameter_schema': {
            'family': { 'type': 'select', 'default': 'gaussian', 'options': ['gaussian','poisson','gamma','inverse_gaussian'], 'help': '分布族。' },
            'link': { 'type': 'select', 'default': 'identity', 'options': ['identity','log','inverse','logit'], 'help': '链接函数。' }
        }
    },
    {
        'name': 'polynomial',
        'display_name': '多项式回归（Polynomial）',
        'algorithm_type': 'regression',
        'description': '通过多项式特征扩展实现非线性拟合。',
        'default_parameters': {
            'degree': 2,
            'include_bias': True
        },
        'parameter_schema': {
            'degree': { 'type': 'number', 'default': 2, 'min': 1, 'step': 1, 'help': '多项式阶数。' },
            'include_bias': { 'type': 'boolean', 'default': True, 'help': '是否包含偏置项。' }
        }
    },
    {
        'name': 'svr',
        'display_name': '支持向量机回归（SVR）',
        'algorithm_type': 'regression',
        'description': '基于支持向量机的回归，鲁棒性强。',
        'default_parameters': {
            'C': 1.0,
            'epsilon': 0.1,
            'kernel': 'rbf'
        },
        'parameter_schema': {
            'C': { 'type': 'number', 'default': 1.0, 'min': 0.01, 'step': 0.1, 'help': '正则化参数。' },
            'epsilon': { 'type': 'number', 'default': 0.1, 'min': 0, 'step': 0.05, 'help': 'ε-不敏感区间宽度。' },
            'kernel': { 'type': 'select', 'default': 'rbf', 'options': ['rbf','linear','poly','sigmoid'], 'help': '核函数类型。' }
        }
    },
    {
        'name': 'knn_regressor',
        'display_name': '最近邻回归（KNN Regressor）',
        'algorithm_type': 'regression',
        'description': '基于邻居的非参数方法。',
        'default_parameters': {
            'n_neighbors': 5,
            'weights': 'uniform',
            'algorithm': 'auto'
        },
        'parameter_schema': {
            'n_neighbors': { 'type': 'number', 'default': 5, 'min': 1, 'step': 1, 'help': '邻居数量。' },
            'weights': { 'type': 'select', 'default': 'uniform', 'options': ['uniform','distance'], 'help': '投票权重策略。' },
            'algorithm': { 'type': 'select', 'default': 'auto', 'options': ['auto','ball_tree','kd_tree','brute'], 'help': '近邻搜索算法。' }
        }
    },
    {
        'name': 'gpr',
        'display_name': '高斯过程回归（GPR）',
        'algorithm_type': 'regression',
        'description': '非参数贝叶斯方法，提供不确定性估计。',
        'default_parameters': {
            'alpha': 1e-10,
            'kernel': 'RBF'
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1e-10, 'step': 1e-10, 'help': '观测噪声加性项。' },
            'kernel': { 'type': 'select', 'default': 'RBF', 'options': ['RBF','Matern','RationalQuadratic','DotProduct'], 'help': '核函数类型。' }
        }
    },
    {
        'name': 'decision_tree_regressor',
        'display_name': '决策树回归（Decision Tree）',
        'algorithm_type': 'regression',
        'description': '树模型，易解释，支持非线性。',
        'default_parameters': {
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1
        },
        'parameter_schema': {
            'max_depth': { 'type': 'number', 'default': None, 'help': '最大深度，null 为不限制。' },
            'min_samples_split': { 'type': 'number', 'default': 2, 'min': 2, 'step': 1, 'help': '内部节点再划分所需最小样本数。' },
            'min_samples_leaf': { 'type': 'number', 'default': 1, 'min': 1, 'step': 1, 'help': '叶子节点最少样本数。' }
        }
    },
    {
        'name': 'bagging_regressor',
        'display_name': 'Bagging 回归（Bagging）',
        'algorithm_type': 'regression',
        'description': '自助聚合的集成方法，降低方差。',
        'default_parameters': {
            'n_estimators': 10,
            'max_samples': 1.0,
            'max_features': 1.0
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 10, 'min': 1, 'step': 1, 'help': '基学习器数量。' },
            'max_samples': { 'type': 'number', 'default': 1.0, 'min': 0.1, 'max': 1.0, 'step': 0.1, 'help': '每个学习器采样的样本占比。' },
            'max_features': { 'type': 'number', 'default': 1.0, 'min': 0.1, 'max': 1.0, 'step': 0.1, 'help': '每个学习器采样的特征占比。' }
        }
    },
    {
        'name': 'random_forest_regressor',
        'display_name': '随机森林回归（Random Forest）',
        'algorithm_type': 'regression',
        'description': '多棵决策树的集成，效果稳定。',
        'default_parameters': {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 100, 'min': 10, 'step': 10, 'help': '树的数量。' },
            'max_depth': { 'type': 'number', 'default': None, 'help': '最大深度，null 为不限制。' },
            'min_samples_split': { 'type': 'number', 'default': 2, 'min': 2, 'step': 1 },
            'min_samples_leaf': { 'type': 'number', 'default': 1, 'min': 1, 'step': 1 }
        }
    },
    # ============== 新增算法 ==============
    {
        'name': 'elastic_net',
        'display_name': '弹性网络回归（ElasticNet）',
        'algorithm_type': 'regression',
        'description': '结合L1与L2正则，兼顾稀疏性与稳定性。',
        'default_parameters': {
            'alpha': 1.0,
            'l1_ratio': 0.5,
            'max_iter': 1000
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1, 'help': '正则化强度。' },
            'l1_ratio': { 'type': 'number', 'default': 0.5, 'min': 0, 'max': 1, 'step': 0.05, 'help': 'L1 与 L2 的权衡。' },
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 }
        }
    },
    {
        'name': 'multi_task_lasso',
        'display_name': '多任务Lasso回归（MultiTaskLasso）',
        'algorithm_type': 'regression',
        'description': '多输出回归的L1正则，联合选择特征。',
        'default_parameters': {
            'alpha': 1.0,
            'max_iter': 1000
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1 },
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 }
        }
    },
    {
        'name': 'multi_task_elastic_net',
        'display_name': '多任务弹性网络（MultiTaskElasticNet）',
        'algorithm_type': 'regression',
        'description': '多输出弹性网络，联合正则。',
        'default_parameters': {
            'alpha': 1.0,
            'l1_ratio': 0.5,
            'max_iter': 1000
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1 },
            'l1_ratio': { 'type': 'number', 'default': 0.5, 'min': 0, 'max': 1, 'step': 0.05 },
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 }
        }
    },
    {
        'name': 'lasso_lars',
        'display_name': 'LARS Lasso 回归（LassoLars）',
        'algorithm_type': 'regression',
        'description': '最小角回归路径的Lasso变体，高维稀疏。',
        'default_parameters': {
            'alpha': 1.0
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1 }
        }
    },
    {
        'name': 'bayesian_regression',
        'display_name': '贝叶斯回归（Bayesian Regression）',
        'algorithm_type': 'regression',
        'description': '贝叶斯线性回归（简单先验）。',
        'default_parameters': {
            'n_iter': 300
        },
        'parameter_schema': {
            'n_iter': { 'type': 'number', 'default': 300, 'min': 100, 'step': 50 }
        }
    },
    {
        'name': 'ransac',
        'display_name': 'RANSAC 回归（RANSACRegressor）',
        'algorithm_type': 'regression',
        'description': '随机采样一致性，鲁棒拟合剔除离群点。',
        'default_parameters': {
            'min_samples': None,
            'residual_threshold': None
        },
        'parameter_schema': {
            'min_samples': { 'type': 'number', 'default': None, 'help': '内点最小样本数，None 为自动。' },
            'residual_threshold': { 'type': 'number', 'default': None, 'help': '残差阈值，None 为自动估计。' }
        }
    },
    {
        'name': 'theil_sen',
        'display_name': 'Theil-Sen 回归（TheilSenRegressor）',
        'algorithm_type': 'regression',
        'description': '非参数鲁棒线性回归，对离群点不敏感。',
        'default_parameters': {
            'random_state': 42
        },
        'parameter_schema': {
            'random_state': { 'type': 'number', 'default': 42, 'help': '随机种子。' }
        }
    },
    {
        'name': 'huber',
        'display_name': 'Huber 回归（HuberRegressor）',
        'algorithm_type': 'regression',
        'description': 'Huber损失的鲁棒线性模型。',
        'default_parameters': {
            'epsilon': 1.35,
            'alpha': 0.0001
        },
        'parameter_schema': {
            'epsilon': { 'type': 'number', 'default': 1.35, 'min': 1.0, 'step': 0.05, 'help': 'Huber 损失阈值。' },
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 }
        }
    },
    {
        'name': 'extra_trees',
        'display_name': '极端随机森林回归（ExtraTreesRegressor）',
        'algorithm_type': 'regression',
        'description': '完全随机划分的树集成，方差低速度快。',
        'default_parameters': {
            'n_estimators': 200,
            'max_depth': None
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 200, 'min': 10, 'step': 10 },
            'max_depth': { 'type': 'number', 'default': None }
        }
    },
    {
        'name': 'adaboost',
        'display_name': 'AdaBoost 回归（AdaBoostRegressor）',
        'algorithm_type': 'regression',
        'description': '提升方法，迭代聚焦难样本。',
        'default_parameters': {
            'n_estimators': 100,
            'learning_rate': 0.1
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 100, 'min': 10, 'step': 10 },
            'learning_rate': { 'type': 'number', 'default': 0.1, 'min': 0.001, 'step': 0.01 }
        }
    },
    {
        'name': 'gbrt',
        'display_name': '梯度提升回归树（GradientBoostingRegressor）',
        'algorithm_type': 'regression',
        'description': '基于残差的梯度提升，强大且稳健。',
        'default_parameters': {
            'n_estimators': 200,
            'learning_rate': 0.1,
            'max_depth': 3
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 200, 'min': 10, 'step': 10 },
            'learning_rate': { 'type': 'number', 'default': 0.1, 'min': 0.001, 'step': 0.01 },
            'max_depth': { 'type': 'number', 'default': 3, 'min': 1, 'step': 1 }
        }
    },
    {
        'name': 'voting_regressor',
        'display_name': '投票回归器（VotingRegressor）',
        'algorithm_type': 'regression',
        'description': '将多个基模型输出平均/加权融合。',
        'default_parameters': {
            'estimators': ['linear_regression','ridge','lasso']
        },
        'parameter_schema': {
            'estimators': { 'type': 'multiselect', 'default': ['linear_regression','ridge','lasso'], 'options': ['linear_regression','ridge','lasso','random_forest_regressor','elastic_net','svr','gbrt','extra_trees'], 'help': '参与投票的基学习器。' }
        }
    },
    {
        'name': 'stacking_regressor',
        'display_name': 'Stacking 回归（StackingRegressor）',
        'algorithm_type': 'regression',
        'description': '多层次集成，元学习器融合。',
        'default_parameters': {
            'estimators': ['ridge','lasso'],
            'final_estimator': 'linear_regression'
        },
        'parameter_schema': {
            'estimators': { 'type': 'multiselect', 'default': ['ridge','lasso'], 'options': ['linear_regression','ridge','lasso','elastic_net','random_forest_regressor','svr','gbrt','extra_trees'], 'help': '一级基学习器集合。' },
            'final_estimator': { 'type': 'select', 'default': 'linear_regression', 'options': ['linear_regression','ridge','lasso','elastic_net'], 'help': '二级元学习器。' }
        }
    },
    {
        'name': 'xgboost',
        'display_name': 'XGBoost 回归（XGBRegressor）',
        'algorithm_type': 'regression',
        'description': '高效梯度提升库。',
        'default_parameters': {
            'n_estimators': 300,
            'learning_rate': 0.1,
            'max_depth': 6,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 300, 'min': 50, 'step': 10 },
            'learning_rate': { 'type': 'number', 'default': 0.1, 'min': 0.001, 'step': 0.01 },
            'max_depth': { 'type': 'number', 'default': 6, 'min': 1, 'step': 1 },
            'subsample': { 'type': 'number', 'default': 0.8, 'min': 0.1, 'max': 1.0, 'step': 0.05 },
            'colsample_bytree': { 'type': 'number', 'default': 0.8, 'min': 0.1, 'max': 1.0, 'step': 0.05 }
        }
    },
    {
        'name': 'lightgbm',
        'display_name': 'LightGBM 回归（LGBMRegressor）',
        'algorithm_type': 'regression',
        'description': '高效GBDT库。',
        'default_parameters': {
            'n_estimators': 300,
            'learning_rate': 0.1,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        },
        'parameter_schema': {
            'n_estimators': { 'type': 'number', 'default': 300, 'min': 50, 'step': 10 },
            'learning_rate': { 'type': 'number', 'default': 0.1, 'min': 0.001, 'step': 0.01 },
            'num_leaves': { 'type': 'number', 'default': 31, 'min': 8, 'step': 1 },
            'subsample': { 'type': 'number', 'default': 0.8, 'min': 0.1, 'max': 1.0, 'step': 0.05 },
            'colsample_bytree': { 'type': 'number', 'default': 0.8, 'min': 0.1, 'max': 1.0, 'step': 0.05 }
        }
    },
    # ================= 追加的新算法（基于 scikit-learn） =================
    {
        'name': 'kernel_ridge',
        'display_name': '核岭回归（KernelRidge）',
        'algorithm_type': 'regression',
        'description': '将岭回归与核技巧结合，拟合非线性关系。',
        'default_parameters': {
            'alpha': 1.0,
            'kernel': 'rbf',
            'gamma': None
        },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 1.0, 'min': 0, 'step': 0.1 },
            'kernel': { 'type': 'select', 'default': 'rbf', 'options': ['linear','rbf','poly','sigmoid','laplacian','chi2'] },
            'gamma': { 'type': 'number', 'default': None }
        }
    },
    {
        'name': 'lars',
        'display_name': '最小角回归（LARS）',
        'algorithm_type': 'regression',
        'description': '高维下高效的线性回归路径算法。',
        'default_parameters': { 'n_nonzero_coefs': None },
        'parameter_schema': {
            'n_nonzero_coefs': { 'type': 'number', 'default': None, 'help': '系数稀疏度，None 表示自动' }
        }
    },
    {
        'name': 'lars_cv',
        'display_name': '最小角回归（LarsCV）',
        'algorithm_type': 'regression',
        'description': '带交叉验证的LARS。',
        'default_parameters': { 'cv': 5 },
        'parameter_schema': {
            'cv': { 'type': 'number', 'default': 5, 'min': 2, 'step': 1, 'help': '交叉验证折数' }
        }
    },
    {
        'name': 'lasso_lars_ic',
        'display_name': 'LassoLarsIC（AIC/BIC）',
        'algorithm_type': 'regression',
        'description': '基于信息准则选择的 LassoLars。',
        'default_parameters': { 'criterion': 'aic' },
        'parameter_schema': {
            'criterion': { 'type': 'select', 'default': 'aic', 'options': ['aic','bic'] }
        }
    },
    {
        'name': 'omp',
        'display_name': '正交匹配追踪（OMP）',
        'algorithm_type': 'regression',
        'description': '稀疏解的贪心算法。',
        'default_parameters': { 'n_nonzero_coefs': None },
        'parameter_schema': {
            'n_nonzero_coefs': { 'type': 'number', 'default': None }
        }
    },
    {
        'name': 'omp_cv',
        'display_name': '正交匹配追踪（OMP-CV）',
        'algorithm_type': 'regression',
        'description': '带交叉验证的 OMP。',
        'default_parameters': { 'cv': 5 },
        'parameter_schema': {
            'cv': { 'type': 'number', 'default': 5, 'min': 2, 'step': 1, 'help': '交叉验证折数' }
        }
    },
    {
        'name': 'elastic_net_cv',
        'display_name': '弹性网络（ElasticNetCV）',
        'algorithm_type': 'regression',
        'description': '带交叉验证选择超参数的弹性网络。',
        'default_parameters': { 'l1_ratio': 0.5, 'cv': 5 },
        'parameter_schema': {
            'l1_ratio': { 'type': 'number', 'default': 0.5, 'min': 0, 'max': 1, 'step': 0.05 },
            'cv': { 'type': 'number', 'default': 5, 'min': 2, 'step': 1 }
        }
    },
    {
        'name': 'lasso_cv',
        'display_name': 'LassoCV',
        'algorithm_type': 'regression',
        'description': '带交叉验证的 Lasso。',
        'default_parameters': { 'cv': 5 },
        'parameter_schema': {
            'cv': { 'type': 'number', 'default': 5, 'min': 2, 'step': 1 }
        }
    },
    {
        'name': 'ridge_cv',
        'display_name': 'RidgeCV',
        'algorithm_type': 'regression',
        'description': '带交叉验证的 Ridge。',
        'default_parameters': { 'cv': 5 },
        'parameter_schema': {
            'cv': { 'type': 'number', 'default': 5, 'min': 2, 'step': 1 }
        }
    },
    {
        'name': 'passive_aggressive',
        'display_name': '被动-激进回归（PassiveAggressiveRegressor）',
        'algorithm_type': 'regression',
        'description': '在线学习的线性模型。',
        'default_parameters': { 'max_iter': 1000, 'loss': 'epsilon_insensitive', 'epsilon': 0.1 },
        'parameter_schema': {
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 },
            'loss': { 'type': 'select', 'default': 'epsilon_insensitive', 'options': ['epsilon_insensitive','squared_epsilon_insensitive'] },
            'epsilon': { 'type': 'number', 'default': 0.1, 'min': 0, 'step': 0.01 }
        }
    },
    {
        'name': 'sgd_regressor',
        'display_name': '随机梯度下降回归（SGDRegressor）',
        'algorithm_type': 'regression',
        'description': '可扩展的线性回归，支持多种正则。',
        'default_parameters': { 'max_iter': 1000, 'alpha': 0.0001, 'penalty': 'l2', 'l1_ratio': 0.15 },
        'parameter_schema': {
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 },
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 },
            'penalty': { 'type': 'select', 'default': 'l2', 'options': ['l2','l1','elasticnet'] },
            'l1_ratio': { 'type': 'number', 'default': 0.15, 'min': 0, 'max': 1, 'step': 0.01 }
        }
    },
    {
        'name': 'quantile_regressor',
        'display_name': '分位数回归（QuantileRegressor）',
        'algorithm_type': 'regression',
        'description': '直接拟合目标分位数。',
        'default_parameters': { 'quantile': 0.5, 'alpha': 0.0001 },
        'parameter_schema': {
            'quantile': { 'type': 'number', 'default': 0.5, 'min': 0, 'max': 1, 'step': 0.01 },
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 }
        }
    },
    {
        'name': 'tweedie',
        'display_name': 'Tweedie 回归（TweedieRegressor）',
        'algorithm_type': 'regression',
        'description': '广义线性模型族，支持多类分布（幂参数 p）。',
        'default_parameters': { 'power': 1.5, 'alpha': 0.0001, 'link': 'auto' },
        'parameter_schema': {
            'power': { 'type': 'number', 'default': 1.5, 'min': 0, 'max': 2, 'step': 0.1 },
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 },
            'link': { 'type': 'select', 'default': 'auto', 'options': ['auto','identity','log'] }
        }
    },
    {
        'name': 'poisson',
        'display_name': '泊松回归（PoissonRegressor）',
        'algorithm_type': 'regression',
        'description': '适合计数型目标的回归。',
        'default_parameters': { 'alpha': 0.0001 },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 }
        }
    },
    {
        'name': 'gamma',
        'display_name': 'Gamma 回归（GammaRegressor）',
        'algorithm_type': 'regression',
        'description': '适合正值偏态分布的目标。',
        'default_parameters': { 'alpha': 0.0001 },
        'parameter_schema': {
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 }
        }
    },
    {
        'name': 'linear_svr',
        'display_name': '线性支持向量回归（LinearSVR）',
        'algorithm_type': 'regression',
        'description': '线性核SVR，适合高维线性近似。',
        'default_parameters': { 'C': 1.0, 'epsilon': 0.0, 'max_iter': 1000 },
        'parameter_schema': {
            'C': { 'type': 'number', 'default': 1.0, 'min': 0.01, 'step': 0.1 },
            'epsilon': { 'type': 'number', 'default': 0.0, 'min': 0, 'step': 0.01 },
            'max_iter': { 'type': 'number', 'default': 1000, 'min': 100, 'step': 100 }
        }
    },
    {
        'name': 'nu_svr',
        'display_name': 'Nu 支持向量回归（NuSVR）',
        'algorithm_type': 'regression',
        'description': '用 ν 控制支持向量比例的 SVR 变体。',
        'default_parameters': { 'nu': 0.5, 'C': 1.0, 'kernel': 'rbf' },
        'parameter_schema': {
            'nu': { 'type': 'number', 'default': 0.5, 'min': 0.01, 'max': 1.0, 'step': 0.01 },
            'C': { 'type': 'number', 'default': 1.0, 'min': 0.01, 'step': 0.1 },
            'kernel': { 'type': 'select', 'default': 'rbf', 'options': ['rbf','linear','poly','sigmoid'] }
        }
    },
    {
        'name': 'radius_neighbors_regressor',
        'display_name': '半径近邻回归（RadiusNeighborsRegressor）',
        'algorithm_type': 'regression',
        'description': '在给定半径内的邻居上进行回归。',
        'default_parameters': { 'radius': 5.0, 'weights': 'distance', 'algorithm': 'auto', 'leaf_size': 30, 'metric': 'minkowski' },
        'parameter_schema': {
            'radius': { 'type': 'number', 'default': 5.0, 'min': 0.1, 'step': 0.1 },
            'weights': { 'type': 'select', 'default': 'distance', 'options': ['uniform','distance'] },
            'algorithm': { 'type': 'select', 'default': 'auto', 'options': ['auto','ball_tree','kd_tree','brute'] },
            'leaf_size': { 'type': 'number', 'default': 30, 'min': 10, 'step': 5 },
            'metric': { 'type': 'select', 'default': 'minkowski', 'options': ['minkowski','euclidean','manhattan','chebyshev'] }
        }
    },
    {
        'name': 'mlp_regressor',
        'display_name': '多层感知机回归（MLPRegressor）',
        'algorithm_type': 'regression',
        'description': '前馈神经网络，能拟合复杂非线性关系。',
        'default_parameters': { 'hidden_layer_sizes': '(100,)', 'activation': 'relu', 'alpha': 0.0001, 'learning_rate_init': 0.001, 'max_iter': 200 },
        'parameter_schema': {
            'hidden_layer_sizes': { 'type': 'text', 'default': '(100,)' },
            'activation': { 'type': 'select', 'default': 'relu', 'options': ['identity','logistic','tanh','relu'] },
            'alpha': { 'type': 'number', 'default': 0.0001, 'min': 0, 'step': 0.0001 },
            'learning_rate_init': { 'type': 'number', 'default': 0.001, 'min': 1e-5, 'step': 0.0005 },
            'max_iter': { 'type': 'number', 'default': 200, 'min': 100, 'step': 50 }
        }
    },
    {
        'name': 'hist_gradient_boosting',
        'display_name': '直方图梯度提升回归（HistGradientBoostingRegressor）',
        'algorithm_type': 'regression',
        'description': '高效的GBDT实现，训练速度快、表现强。',
        'default_parameters': { 'learning_rate': 0.1, 'max_depth': None, 'max_iter': 200, 'l2_regularization': 0.0 },
        'parameter_schema': {
            'learning_rate': { 'type': 'number', 'default': 0.1, 'min': 0.001, 'step': 0.01 },
            'max_depth': { 'type': 'number', 'default': None },
            'max_iter': { 'type': 'number', 'default': 200, 'min': 50, 'step': 10 },
            'l2_regularization': { 'type': 'number', 'default': 0.0, 'min': 0, 'step': 0.001 }
        }
    },
    {
        'name': 'pls_regression',
        'display_name': '偏最小二乘回归（PLSRegression）',
        'algorithm_type': 'regression',
        'description': '在高维相关特征中进行降维与回归的联合建模。',
        'default_parameters': { 'n_components': 2, 'scale': True },
        'parameter_schema': {
            'n_components': { 'type': 'number', 'default': 2, 'min': 1, 'step': 1 },
            'scale': { 'type': 'boolean', 'default': True }
        }
    },
    # 可选外部库：CatBoost
    {
        'name': 'catboost',
        'display_name': 'CatBoost 回归（CatBoostRegressor）',
        'algorithm_type': 'regression',
        'description': '基于对称树的梯度提升（需安装 catboost）。',
        'default_parameters': { 'iterations': 500, 'learning_rate': 0.05, 'depth': 6 },
        'parameter_schema': {
            'iterations': { 'type': 'number', 'default': 500, 'min': 50, 'step': 10 },
            'learning_rate': { 'type': 'number', 'default': 0.05, 'min': 0.001, 'step': 0.005 },
            'depth': { 'type': 'number', 'default': 6, 'min': 2, 'max': 16, 'step': 1 }
        }
    },
]


class Command(BaseCommand):
    help = "Seed common regression ML algorithms into MLAlgorithm table"

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Clear existing regression algorithms before seeding')

    def handle(self, *args, **options):
        if options['reset']:
            deleted = MLAlgorithm.objects.filter(algorithm_type='regression').delete()
            self.stdout.write(self.style.WARNING(f"Cleared existing regression algorithms: {deleted[0]}"))

        created, updated = 0, 0
        for item in REGRESSION_ALGORITHMS:
            obj, is_created = MLAlgorithm.objects.update_or_create(
                name=item['name'],
                defaults={
                    'display_name': item['display_name'],
                    'algorithm_type': item['algorithm_type'],
                    'description': item['description'],
                    'default_parameters': item['default_parameters'],
                    'parameter_schema': item.get('parameter_schema', {}),
                    'is_active': True,
                    'is_premium': False,
                }
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded regression algorithms. Created: {created}, Updated: {updated}"))


