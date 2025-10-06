from app.models.ai_analysis import AIAnalysisResult
from app.models.training_video import TrainingVideo
from app import db
from datetime import datetime
import random
import time
import json

class AIService:
    
    @staticmethod
    def process_video_mock(video_id):
        """Xử lý video bằng AI (Mock/Giả lập)"""
        try:
            video = TrainingVideo.query.get(video_id)
            if not video:
                raise Exception("Video không tồn tại")
            
            # Cập nhật trạng thái đang xử lý
            video.processing_status = 'processing'
            db.session.commit()
            
            # Giả lập thời gian xử lý (2-5 giây)
            time.sleep(random.uniform(2, 5))
            
            # Lấy thông tin bài võ để tạo kết quả
            routine = video.routine
            weapon_name = routine.weapon.weapon_name_en if routine.weapon else "Unknown"
            
            # Generate mock results
            analysis_result = AIAnalysisResult(
                video_id=video_id,
                weapon_detected=weapon_name,
                weapon_confidence=round(random.uniform(85, 98), 2),
                overall_score=round(random.uniform(60, 95), 2),
                technique_score=round(random.uniform(55, 95), 2),
                posture_score=round(random.uniform(60, 95), 2),
                timing_score=round(random.uniform(65, 95), 2),
                detailed_feedback=AIService.generate_mock_feedback(weapon_name),
                key_frames=AIService.generate_mock_keyframes(video.duration_seconds),
                errors_detected=AIService.generate_mock_errors(),
                ai_model_version="v1.0.0-mock",
                processing_time_seconds=round(random.uniform(2, 5), 2),
                analyzed_at=datetime.utcnow()
            )
            
            db.session.add(analysis_result)
            
            # Cập nhật trạng thái video
            video.processing_status = 'completed'
            video.processed_at = datetime.utcnow()
            
            db.session.commit()
            
            return analysis_result
            
        except Exception as e:
            db.session.rollback()
            # Cập nhật trạng thái thất bại
            video.processing_status = 'failed'
            db.session.commit()
            raise Exception(f"Lỗi khi xử lý AI: {str(e)}")
    
    @staticmethod
    def generate_mock_feedback(weapon_name):
        """Tạo feedback giả lập"""
        feedbacks = {
            "Sword": {
                "strengths": [
                    "Tư thế cầm kiếm đúng kỹ thuật",
                    "Động tác chém có lực và chính xác",
                    "Bước di chuyển ổn định"
                ],
                "weaknesses": [
                    "Cần cải thiện tốc độ ra đòn",
                    "Một số động tác còn hơi cứng",
                    "Chưa đồng bộ giữa tay và chân"
                ],
                "suggestions": [
                    "Luyện tập thêm về tốc độ phản xạ",
                    "Tăng cường độ dẻo dai cơ bắp",
                    "Tập trung vào sự mượt mà của động tác"
                ]
            },
            "Staff": {
                "strengths": [
                    "Xoay côn tròn và liên tục",
                    "Kiểm soát tốc độ tốt",
                    "Di chuyển linh hoạt"
                ],
                "weaknesses": [
                    "Một số động tác chưa đủ mạnh",
                    "Tư thế đứng chưa vững",
                    "Cần cải thiện độ chính xác"
                ],
                "suggestions": [
                    "Luyện thêm về sức mạnh cổ tay",
                    "Tập trung vào trọng tâm cơ thể",
                    "Thực hành chậm để nắm vững kỹ thuật"
                ]
            },
            "default": {
                "strengths": [
                    "Thực hiện đầy đủ các động tác",
                    "Tư thế cơ bản đúng",
                    "Tinh thần tập luyện tốt"
                ],
                "weaknesses": [
                    "Cần cải thiện kỹ thuật cơ bản",
                    "Tốc độ chưa đồng đều",
                    "Một số động tác cần chính xác hơn"
                ],
                "suggestions": [
                    "Luyện tập đều đặn mỗi ngày",
                    "Xem kỹ video mẫu để cải thiện",
                    "Tập trung vào từng động tác riêng lẻ"
                ]
            }
        }
        
        feedback = feedbacks.get(weapon_name, feedbacks["default"])
        
        return {
            "summary": f"Phân tích cho bài võ {weapon_name}",
            "strengths": feedback["strengths"],
            "weaknesses": feedback["weaknesses"],
            "suggestions": feedback["suggestions"],
            "overall_comment": "Bạn đã có sự tiến bộ rõ rệt. Hãy tiếp tục luyện tập và cải thiện những điểm yếu."
        }
    
    @staticmethod
    def generate_mock_keyframes(duration_seconds):
        """Tạo key frames giả lập"""
        num_frames = random.randint(5, 10)
        key_frames = []
        
        for i in range(num_frames):
            timestamp = random.randint(0, duration_seconds)
            key_frames.append({
                "timestamp": timestamp,
                "description": f"Động tác quan trọng tại giây {timestamp}",
                "score": round(random.uniform(60, 95), 2),
                "note": random.choice([
                    "Tư thế tốt",
                    "Cần cải thiện",
                    "Động tác chuẩn",
                    "Lực chưa đủ",
                    "Tốc độ hợp lý"
                ])
            })
        
        return sorted(key_frames, key=lambda x: x['timestamp'])
    
    @staticmethod
    def generate_mock_errors():
        """Tạo lỗi phát hiện giả lập"""
        possible_errors = [
            {"type": "posture", "description": "Tư thế đứng chưa vững tại giây 15", "severity": "medium"},
            {"type": "technique", "description": "Động tác tay chưa chính xác tại giây 23", "severity": "high"},
            {"type": "timing", "description": "Nhịp độ chưa đồng đều tại giây 30-35", "severity": "low"},
            {"type": "weapon_grip", "description": "Cầm binh khí chưa đúng kỹ thuật", "severity": "medium"},
            {"type": "movement", "description": "Di chuyển chưa mượt mà tại giây 42", "severity": "low"}
        ]
        
        num_errors = random.randint(0, 3)
        return random.sample(possible_errors, num_errors)
