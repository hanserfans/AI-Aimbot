
# 双GPU优化配置
import onnxruntime as ort
import os
import gc
import threading
import queue
import time

class DualGPUManager:
    """双GPU管理器"""
    
    def __init__(self):
        self.nvidia_session = None
        self.amd_session = None
        self.cpu_session = None
        self.current_gpu = 0  # 0: NVIDIA, 1: AMD
        self.inference_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
    def create_sessions(self, model_path):
        """创建多GPU会话"""
        
        # 优化的会话选项
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        so.enable_mem_pattern = True
        so.enable_cpu_mem_arena = True
        so.intra_op_num_threads = 2  # 减少每个会话的线程数
        so.inter_op_num_threads = 1
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        try:
            # NVIDIA GPU会话
            cuda_options = {
                'device_id': 0,
                'arena_extend_strategy': 'kSameAsRequested',
                'gpu_mem_limit': 1536 * 1024 * 1024,  # 1.5GB限制
                'cudnn_conv_algo_search': 'HEURISTIC',
            }
            self.nvidia_session = ort.InferenceSession(
                model_path, 
                sess_options=so, 
                providers=[('CUDAExecutionProvider', cuda_options)]
            )
            print("[INFO] ✅ NVIDIA GPU会话创建成功")
            
        except Exception as e:
            print(f"[WARNING] NVIDIA GPU会话创建失败: {e}")
        
        try:
            # AMD GPU会话（DirectML）
            dml_options = {'device_id': 1}  # 尝试使用第二个设备
            self.amd_session = ort.InferenceSession(
                model_path,
                sess_options=so,
                providers=[('DmlExecutionProvider', dml_options)]
            )
            print("[INFO] ✅ AMD GPU会话创建成功")
            
        except Exception as e:
            print(f"[WARNING] AMD GPU会话创建失败: {e}")
        
        # CPU备用会话
        self.cpu_session = ort.InferenceSession(
            model_path,
            sess_options=so,
            providers=['CPUExecutionProvider']
        )
        print("[INFO] ✅ CPU备用会话创建成功")
    
    def run_inference_balanced(self, input_data):
        """负载均衡推理"""
        
        # 选择可用的GPU
        if self.current_gpu == 0 and self.nvidia_session:
            try:
                result = self.nvidia_session.run(None, input_data)
                self.current_gpu = 1  # 切换到下一个GPU
                return result
            except Exception as e:
                print(f"[WARNING] NVIDIA GPU推理失败: {e}")
        
        if self.current_gpu == 1 and self.amd_session:
            try:
                result = self.amd_session.run(None, input_data)
                self.current_gpu = 0  # 切换回NVIDIA
                return result
            except Exception as e:
                print(f"[WARNING] AMD GPU推理失败: {e}")
        
        # 备用CPU推理
        if self.cpu_session:
            result = self.cpu_session.run(None, input_data)
            return result
        
        raise Exception("所有推理会话都不可用")
    
    def run_inference_parallel(self, input_data):
        """并行推理（实验性）"""
        
        def nvidia_inference():
            if self.nvidia_session:
                try:
                    result = self.nvidia_session.run(None, input_data)
                    self.result_queue.put(('nvidia', result))
                except Exception as e:
                    self.result_queue.put(('nvidia', None))
        
        def amd_inference():
            if self.amd_session:
                try:
                    result = self.amd_session.run(None, input_data)
                    self.result_queue.put(('amd', result))
                except Exception as e:
                    self.result_queue.put(('amd', None))
        
        # 启动并行推理
        nvidia_thread = threading.Thread(target=nvidia_inference)
        amd_thread = threading.Thread(target=amd_inference)
        
        nvidia_thread.start()
        amd_thread.start()
        
        # 等待第一个完成的结果
        try:
            gpu_name, result = self.result_queue.get(timeout=1.0)
            if result is not None:
                return result
        except queue.Empty:
            pass
        
        # 等待线程完成
        nvidia_thread.join(timeout=0.5)
        amd_thread.join(timeout=0.5)
        
        # 如果都失败，使用CPU
        if self.cpu_session:
            return self.cpu_session.run(None, input_data)
        
        raise Exception("所有推理会话都失败")

# 全局双GPU管理器
dual_gpu_manager = None

def initialize_dual_gpu(model_path):
    """初始化双GPU管理器"""
    global dual_gpu_manager
    
    # 设置环境变量
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['MKL_NUM_THREADS'] = '2'
    
    dual_gpu_manager = DualGPUManager()
    dual_gpu_manager.create_sessions(model_path)
    
    return dual_gpu_manager

def run_optimized_inference(input_data, use_parallel=False):
    """运行优化的推理"""
    global dual_gpu_manager
    
    if dual_gpu_manager is None:
        raise Exception("双GPU管理器未初始化")
    
    if use_parallel:
        return dual_gpu_manager.run_inference_parallel(input_data)
    else:
        return dual_gpu_manager.run_inference_balanced(input_data)
