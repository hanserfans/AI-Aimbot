
# 优化的ONNX配置
import onnxruntime as ort
import os

# 设置环境变量优化内存
os.environ['OMP_NUM_THREADS'] = '16'  # 优化OpenMP线程数（32核CPU）
os.environ['MKL_NUM_THREADS'] = '16'  # 优化MKL线程数
os.environ['NUMEXPR_NUM_THREADS'] = '16'  # 优化NumExpr线程数

def create_optimized_onnx_session(model_path, use_dual_gpu=True):
    """创建优化的ONNX会话"""
    
    # 优化的会话选项
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.enable_mem_pattern = True
    so.enable_cpu_mem_arena = True
    so.intra_op_num_threads = 16  # 优化线程数以充分利用32核CPU
    so.inter_op_num_threads = 8   # 增加并行操作线程数
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    
    # 提供者配置
    providers = []
    
    # NVIDIA GPU配置（优化显存使用）
    cuda_options = {
        'device_id': 0,
        'arena_extend_strategy': 'kNextPowerOfTwo',  # 更激进的内存分配策略
        'gpu_mem_limit': 6 * 1024 * 1024 * 1024,  # 6GB限制（RTX 4060适配）
        'cudnn_conv_algo_search': 'EXHAUSTIVE',  # 使用最优算法
        'do_copy_in_default_stream': True,  # 启用默认流复制
        'cudnn_conv_use_max_workspace': True,  # 使用最大工作空间
    }
    providers.append(('CUDAExecutionProvider', cuda_options))
    
    # AMD GPU配置（如果需要双GPU）
    if use_dual_gpu:
        dml_options = {'device_id': 1}
        providers.append(('DmlExecutionProvider', dml_options))
    
    # CPU备用
    providers.append('CPUExecutionProvider')
    
    try:
        session = ort.InferenceSession(model_path, sess_options=so, providers=providers)
        print(f"[INFO] ONNX会话创建成功，使用提供者: {session.get_providers()}")
        return session
    except Exception as e:
        print(f"[ERROR] ONNX会话创建失败: {e}")
        # 备用CPU会话
        return ort.InferenceSession(model_path, sess_options=so, providers=['CPUExecutionProvider'])
