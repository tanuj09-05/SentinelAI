""" Overall flow of camera_manager.py:

Camera
   │
   ▼
Capture Thread
   │
   ▼
Latest Frame
   │
   ▼
YOLO Detection
   │
   ▼
Face Recognition (Background)
   │
   ▼
Restricted Zone Check
   │
   ▼
Intrusion?
   │
   ▼
Loitering?
   │
   ▼
Save Event
   │
   ▼
Email Alert
   │
   ▼
Dashboard Update

"""

""" There r only 2 main classes in this file:
1. UserCameraThread: Ye class har user ke liye ek alag thread create krta hai jo camera feed ko process krta hai.
2. CameraManager: Ye khud camera nahi chalata.Ye sirf bolta hai

"Is user ka thread bana hua hai kya?"

Agar nahi
↓
Thread bana do.

Agar bana hua hai
↓
Wahi return kar do.
"""
import cv2
import time  # Python ka built-in time module use kr rhe hain
"""
Example
time.time()

Output: 1751600000.2134

Ye koi normal clock nahi hai.
Ye Unix Timestamp hota hai.

Matlab  1 Jan 1970 se abhi tak kitne seconds beet gaye.
"""
from threading import Thread, Lock
"""
## Pehle Thread samjho : Normally Python aise chalta hai

Step 1
↓
Step 2
↓
Step 3
↓
Step 4

Ek kaam khatam.Phir doosra.Lekin surveillance me ye possible nahi.
Camera continuously chal raha hai.Email bhi bhejni hai.Database bhi save karna hai.
Browser ko frame bhi bhejna hai.Face Recognition bhi karni hai.Sab ek saath.

Isliye ->
Main Thread
Camera Thread
Recognition Thread
Email Thread

Sab parallel chalenge.

Isi liye
class UserCameraThread(Thread):

likha hai.Matlab
Ye class ek thread banegi.

## Lock kya hai? : Ye beginners ignore kar dete hain.Socho
Do thread ek hi variable change kar rahe hain.
people_count=5

Camera thread
↓
6

Email thread
↓
7

Dono same time likhenge.Result corrupt ho sakta hai.
Lock bolta hai. Ek time par sirf ek thread andar aa sakta hai.

Example :
Without Lock

Thread A
↓
Read value
↓
5

Isi time

Thread B
↓
Read value
↓
5

Ab

A
↓
6

B
↓
6

Expected : 7

Mila : 6

Data loss.
Lock lagane ke baad

Thread A
↓
Lock
↓
Update
↓
Unlock
↓
Thread B


Safe
"""
import numpy as np
"""
Computer image ko image ki tarah nahi dekhta.Wo matrix dekhta hai.

Example:
2×2 grayscale image

50   80
120 255

Ye actually NumPy array hai.
Color image:

[
 [[255,0,0],[0,255,0]],

 [[0,0,255],[255,255,255]]
]

Har pixel [R,G,B] store karta hai.
"""
from datetime import datetime
"""
Datetime kya hai? :
Ye Python ka built-in module hai jo date aur time ko human-readable format me handle karta hai.

Difference dekho: time.time()
Output: 1751612456.231

Ye sirf timestamp hai.

Lekin : datetime.now()

Output: 2026-07-04 13:45:21
Ye insaan ke padhne layak format hai.

Sentinel AI me iska use. Jab intrusion detect hoti hai:
Person entered restricted zone.Database me save karna hai.
To timestamp aise save hoga: 2026-07-04 13:45:21
Email me bhi yehi dikhega.

Example: ⚠ Intrusion Detected

Time:
04 Jul 2026
13:45:21

Isliye datetime import hua hai.
"""
from concurrent.futures import ThreadPoolExecutor
"""
Pehle problem samjho :
Suppose camera chal raha hai.Ek frame aaya.Face recognition start hui.
Agar face recognition me 2 second lag gaye to...

Frame 1
↓
Recognition
↓
2 sec wait
↓
Frame 2

Camera lag karega.

Solution?
Background me alag thread me chala do.

Isi ka kaam hai: ThreadPoolExecutor

Ye ek thread manager hai.

Example: Tumhare paas 100 kaam hain.

Without Executor ->

Work 1
↓
Work 2
↓
Work 3
↓
Work 4

Ek-ek karke.

With Executor ->

Worker 1
↓
Task A

Worker 2
↓
Task B

Worker 3
↓
Task C

Sab parallel.

Sentinel AI me :

Socho 
YOLO detect karta hai
↓
Face Recognition
↓
Email
↓
Database

Ye sab ek hi thread me karoge to FPS gir jayega. Isliye

Main Camera Thread
↓
Frame Process
↓
Executor
↓
Recognition Thread
↓
Email Thread
↓
Save Thread

Camera smooth chalta rehta hai.
"""
from config import RESTRICTED_ZONE
"""
config.py :
Ye project ka settings file hota hai.Usme kuch aisa hoga:

RESTRICTED_ZONE = [
    (120,100),
    (550,100),
    (550,400),
    (120,400)
]

Ye polygon hai.Matlab Restricted area.

Diagram:

+---------------------------+

        Camera View

        _________
       |         |
       | Zone    |
       |         |
       |_________|

+---------------------------+

Ab agar koi person is rectangle ke andar aaya
↓
Intrusion.

Achhi practice kya hai? 

Ye line mat likho: restricted_zone = [...]
Har file me.Ek hi jagah define karo.
Phir import karo.

Isi liye : from config import RESTRICTED_ZONE
"""
from core.detector import detect
"""
Ye project ka AI brain connect kar raha hai.
detector.py :ke andar likely function hai ->def detect(frame):
Ye frame lega.YOLO chalayega.Objects return karega.

Example :
Input :
Frame
↓
YOLO
↓
Output :
[
 Person,
 Car,
 Helmet
]

Aur har object ke saath
Class
Confidence
Bounding Box
hoga.

Example:
[
{
"class":"person",
"confidence":0.94,
"box":[120,80,250,400]
}
]

Camera Manager khud detect nahi karta. Wo sirf bolta hai
detections = detect(frame)
"""
from core.event_engine import check_intrusion
"""
YOLO sirf ye bolta hai.Person mila.Bas.Lekin Sentinel AI ko ye nahi chahiye.
Usko chahiye

Kya person restricted area me hai?
Ye AI ka kaam nahi hai.Ye business logic hai.

Isi liye : check_intrusion()

banaya gaya.

Flow dekho :
Camera
↓
YOLO
↓
Person detected
↓
check_intrusion()
↓
YES
↓
Create Event

Ye function probably check karta hoga : pointPolygonTest(...)
ya Bounding Box Center Polygon ke andar hai ya nahi.

Agar hai
↓
True

Nahi
↓
False
"""
from core.alert_manager import save_intrusion_image
"""
alert_manager.py file ke andar ek function hai:save_intrusion_image(...)
Iska kaam hai: Intrusion detect hote hi evidence image save karna.

Real Flow:
Suppose camera ne ye detect kiya:

Person
↓
Restricted Zone
↓
Intrusion

Ab sirf alert bhejna enough nahi hai.Evidence bhi chahiye.
To ye function kuch aisa karega: save_intrusion_image(frame)

Result :
intrusions/
2026-07-04_13-45-22.jpg

Save ho gaya.

Real World :
CCTV me jab motion detect hota hai
↓
Screenshot save hota hai.

Ye wahi kaam hai.
"""
from core.email_alert import send_intrusion_email
"""
Ye function intrusion hone ke baad mail bhejta hai.
Flow:
Camera
↓
YOLO
↓
Intrusion
↓
Screenshot Save
↓
Email

Mail kuch aisa ho sakta hai:
⚠ Intrusion Detected
Time: 13:45
Location: Restricted Zone

Attachment:
image.jpg
"""
from database.database import save_event, DATABASE_PATH
# save_event -> Event ko database me save karta hai.
# DATABASE_PATH -> SQLite database ka location/path.

import sqlite3
# SQLite database ke saath connect aur queries run karne ke liye.
from database.user import get_user_settings
# User ki surveillance settings (camera, alerts, zones, etc.) load karta hai.

class UserCameraThread(Thread):
# Har user ke camera ko alag thread me run karne wali class.
# Isse multiple users ke cameras ek saath handle ho sakte hain.
    
    def __init__(self, user_id):

        """
        Purpose:
        Naya camera thread initialize krna user ke liye.
        Parameters:
        user_id -> Jis user ka camera start krna hai uska ID.
        """
        super().__init__()
        # Parent Thread class ko initialize karta hai.
        # Iske bina thread properly work nahi karega.
        self.user_id = user_id
        # Current thread kis user ka hai, uska ID store karta hai.
        
        self.daemon = True
        # Daemon thread background me chalta hai aur main program band hone pr khud band ho jata hai
        # https://chatgpt.com/s/t_6a48d9b359fc8191bf0c0f27beb2eada
        self.last_accessed = time.time()
        # Last time camera kab access hua tha uska timestamp.
        # Inactive camera ko automatically stop karne me help karta hai.
        self.latest_jpeg = None
        # Browser ko bhejne ke liye latest processed JPEG frame store hoga.
        
        self.latest_status = {
            "people": 0,
            "intrusion": False,
            "camera": "offline",
            "latency": 0,
            "fps": 0,
            "loitering_alert": False,
            "max_people": 0,
        }
        # Frontend dashboard ke liye live camera statistics.
        #
        # people           -> Current detected people
        # intrusion        -> Restricted zone breach hui ya nahi
        # camera           -> Camera status (online/offline)
        # latency          -> Frame process hone ka time
        # fps              -> Current Frames Per Second
        # loitering_alert  -> Koi person zyada der se zone me hai ya nahi
        # max_people       -> Maximum people detected

        self.running = True
        # https://chatgpt.com/s/t_6a48dad5af7481918a283475f9e4021b

        # Tracking states (Kon kab aaya aur kahan hai)
        self.active_zone_tracks = {}  # track_id -> entry_time (float)
        # Track ID ke saath entry time store karta hai.
        # Loitering detection ke liye use hota hai.
        self.loitering_alerted = set()  
        # un logo ki list jinka loitering alert ja chuka hai aur duplicates alert rokta hai.
        self.recognized_faces = {}  # track_id -> face details (name, is_known)
        # Recognized faces ko cache karta hai.
        # Baar-baar face recognition chalane ki zarurat nahi padti.
        self.recognition_attempts = {}  # track_id -> int (kitni baar try kiya)
        # Har track ke face recognition attempts count karta hai.
        self.recognition_in_progress = set()  # track_id -> is processing async?
        # Jo tracks currently recognize ho rahe hain unko store karta hai.
        # Ek hi person par multiple recognition threads chalne se bachata hai.
        self._last_processed_frame_id = None
        # Same frame ko dobara process hone se rokta hai.

        # Initial loading screen (black frame) bana rhe hain
        self._black_frame = self._generate_black_frame()
        # Camera start hone se pehle loading/blank frame generate karta hai.
        self.latest_jpeg = self._black_frame
        # Starting me browser ko black/loading frame dikhaya jayega.

        # Camera se raw frames nikalne ke liye variables
        self._latest_raw_frame = None
        # Camera se aaya latest raw (unprocessed) frame store karta hai.
        self._capture_running = False
        # Camera capture thread chal raha hai ya nahi, uska status.
        self._capture_thread = None
        # Camera capture thread ka reference store karega.

        # ThreadPoolExecutor background tasks (email, database) ko fast execute krne ke liye
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Dashboard status fast load krne ke liye purane events count kr rhe hain
        self._cache_total_events()

    def _cache_total_events(self):
        """
        Purpose:
        Database se total events count krke memory me save krna taki baar-baar DB query na krni pde.
        """
        try:
            with sqlite3.connect(DATABASE_PATH, timeout=5) as db_connection:
                database_cursor = db_connection.cursor()
                database_cursor.execute(
                    "SELECT COUNT(*) FROM events WHERE user_id = ?", (self.user_id,)
                )

                # fetchone()[0] pehla result deta hai jo ki number of rows (count) hota hai
                self.latest_status["total_events"] = database_cursor.fetchone()[0]
        except Exception:
            self.latest_status["total_events"] = 0

    def _increment_total_events(self):
        """
        Purpose:
        Total events counter ko badhana jab naya event aaye.
        """
        if "total_events" in self.latest_status:
            self.latest_status["total_events"] += 1

    def _generate_black_frame(self, text="Camera Loading..."):
        """
        Purpose:
        Ek plain black image banana text ke sath (offline/loading status dikhane ke liye).
        """
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)

        # Image pr text likh rhe hain
        cv2.putText(
            black_image,
            text,
            (180, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (80, 80, 80),
            2,
        )

        # Image ko JPEG me convert krke bytes me store kr rhe hain
        _, jpeg_buffer = cv2.imencode(".jpg", black_image)
        return jpeg_buffer.tobytes()

    def run(self):
        """
        Purpose:
        Camera stream start krna aur frame by frame processing handle krna.
        """
        # User ki settings database se la rhe hain
        user_settings = get_user_settings(self.user_id)

        if not user_settings:
            # Agar settings nhi mili toh error dikhayenge
            self.latest_status["camera"] = "ERROR: No Settings"
            self.latest_jpeg = self._generate_black_frame("No Camera Settings")
            self.running = False
            return

        # Tuple unpacking: Settings array me se values extract kr rhe hain
        (
            settings_id,
            settings_user_id,
            smtp_host,
            smtp_port,
            smtp_username,
            smtp_password,
            sender_email,
            receiver_email,
            camera_source,
            camera_index,
            rtsp_url,
            created_at,
            updated_at,
        ) = user_settings

        # Check kr rhe hain ki RTSP use krna hai ya webcam (index 0, 1 etc)
        camera_path = rtsp_url if camera_source == "rtsp" else (camera_index or 0)

        # OpenCV se camera open kr rhe hain
        camera = cv2.VideoCapture(camera_path)

        if not camera.isOpened():
            self.latest_status["camera"] = "OFFLINE"
            self.latest_jpeg = self._generate_black_frame("Camera Offline")
            self.running = False
            return

        self.latest_status["camera"] = "online"

        # Ek alag thread start kr rhe hain jo lag (delay) rokne ke liye
        # frames jaldi-jaldi nikalta rhega
        self._capture_running = True
        self._capture_thread = Thread(
            target=self._capture_loop, args=(camera,), daemon=True
        )
        self._capture_thread.start()

        frame_count = 0
        last_fps_time = time.time()

        while self.running:
            start_time = time.time()

            # Agar 15 seconds tak kisi ne camera feed nhi dekhi, toh process stop kr denge memory bachane ke liye
            if time.time() - self.last_accessed > 15:
                break

            current_frame = self._latest_raw_frame

            # Agar camera ne frame nhi diya ya same frame hai toh thoda wait krenge
            if current_frame is None or id(current_frame) == self._last_processed_frame_id:
                time.sleep(0.01)
                continue
            
            self._last_processed_frame_id = id(current_frame)

            # Original frame ko copy kr rhe hain taki processing karte time asli frame corrupt na ho
            processing_frame = current_frame.copy()
            self.latest_status["camera"] = "online"

            # YOLO model se log (persons) detect kr rhe hain
            # Ye function updated frame, total log aur unke boxes return karta hai
            processing_frame, total_people, bounding_boxes, track_ids = detect(
                processing_frame
            )

            # Status object ko update kr rhe hain
            self.latest_status["people"] = total_people
            self.latest_status["max_people"] = max(
                self.latest_status.get("max_people", 0), total_people
            )

            # ----- PROCESSING STEPS -----
            self._draw_faces_and_dispatch(processing_frame, bounding_boxes, track_ids)
            self._draw_restricted_zone(processing_frame)
            self._handle_intrusions_and_loitering(
                processing_frame, bounding_boxes, track_ids
            )
            self._handle_exits(track_ids)
            self._cleanup_old_faces(track_ids)

            # Result frame ko wapas JPEG me convert kr rhe hain
            _, jpeg_buffer = cv2.imencode(".jpg", processing_frame)
            self.latest_jpeg = jpeg_buffer.tobytes()

            # Processing me kitna time laga (Latency) calculate kr rhe hain
            latency_ms = int((time.time() - start_time) * 1000)
            self.latest_status["latency"] = latency_ms

            # FPS (Frames per second) calculate kr rhe hain
            frame_count += 1
            if time.time() - last_fps_time >= 1.0:
                self.latest_status["fps"] = frame_count
                frame_count = 0
                last_fps_time = time.time()

        # Loop khatam hone pr sab cleanup kr denge
        self._capture_running = False
        camera.release()
        self.executor.shutdown(wait=False)
        self.running = False

    def _draw_faces_and_dispatch(self, frame, bounding_boxes, track_ids):
        """
        Purpose:
        Detected logon ka face recognise krne ke liye background thread me dispatch krna
        aur jo faces pehle se recognized hain unke naam screen pr draw krna.
        """
        for box, track_id in zip(bounding_boxes, track_ids):
            # Agar person ka face pehle identify nhi hua toh async process me daalo
            if track_id not in self.recognized_faces and track_id not in self.recognition_in_progress:
                attempts = self.recognition_attempts.get(track_id, 0)
                if attempts < 10:
                    self.recognition_in_progress.add(track_id)
                    self.executor.submit(
                        self._async_recognize_face, track_id, frame.copy(), box
                    )
                else:
                    self.recognized_faces[track_id] = {
                        "name": "UNKNOWN PERSON",
                        "conf": 0.0,
                        "is_known": False,
                    }

            # Frame pr naam likh rhe hain agar recognize ho gaya hai
            if track_id in self.recognized_faces:
                face_info = self.recognized_faces[track_id]
                x1, y1, x2, y2 = map(int, box)

                label_text = (
                    f"{face_info['name']} ({face_info['conf']:.2f})"
                    if face_info["conf"] > 0
                    else face_info["name"]
                )

                text_color = (255, 255, 0) if face_info["is_known"] else (0, 165, 255)
                cv2.putText(
                    frame,
                    label_text,
                    (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    text_color,
                    2,
                )

    def _async_recognize_face(self, track_id, frame, box):
        """
        Purpose:
        Background me heavy face recognition run krna bina FPS giraye.
        """
        try:
            from core.face_manager import get_face_manager
            face_manager = get_face_manager()
            if not face_manager:
                return

            recognized_name, confidence = face_manager.match_face(
                self.user_id, frame, crop_box=box
            )

            if recognized_name:
                self.recognized_faces[track_id] = {
                    "name": recognized_name,
                    "conf": confidence,
                    "is_known": True,
                }
            elif confidence > 0.0:
                self.recognized_faces[track_id] = {
                    "name": "UNKNOWN PERSON",
                    "conf": confidence,
                    "is_known": False,
                }
                
            self.recognition_attempts[track_id] = self.recognition_attempts.get(track_id, 0) + 1
        finally:
            if track_id in self.recognition_in_progress:
                self.recognition_in_progress.remove(track_id)

    def _draw_restricted_zone(self, frame):
        """
        Purpose:
        Camera frame pr red color ka restricted area (bounding box) draw krna.
        """
        zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE

        # Red rectangle draw kr rhe hain
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 0, 255), 2)
        cv2.putText(
            frame,
            "Restricted Zone",
            (zone_x1, zone_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    def _handle_intrusions_and_loitering(self, frame, bounding_boxes, track_ids):
        """
        Purpose:
        Check krna ki koi restricted zone me aya hai ya zyada der ruka hai (loitering).
        Agar aisa hai toh alert save krna aur email bhejna.
        """
        intruding_ids = check_intrusion(bounding_boxes, track_ids)
        self.latest_status["intrusion"] = len(intruding_ids) > 0

        current_time = time.time()
        loitering_active = False

        for track_id in intruding_ids:
            # Person ki details nikalo
            default_face = {"name": "UNKNOWN (No Face)", "is_known": False}
            face_info = self.recognized_faces.get(track_id, default_face)
            recognized_name = face_info["name"]
            is_known = face_info["is_known"]

            # SCENARIO 1: Koi naya person zone me aya
            if track_id not in self.active_zone_tracks:
                # Uske aane ka time save kr lo
                self.active_zone_tracks[track_id] = current_time
                entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Database aur email task ko background thread me dal rhe hain
                self.executor.submit(
                    self._save_and_alert_event,
                    frame.copy(),
                    track_id,
                    "Intrusion",
                    recognized_name,
                    is_known,
                    entry_time=entry_timestamp,
                )

            # SCENARIO 2: Loitering (Person 15 seconds se zyada zone me ruk gaya hai)
            time_in_zone = current_time - self.active_zone_tracks[track_id]

            if time_in_zone > 15:
                loitering_active = True

                # Screen pr bada sa red warning dikhayenge
                cv2.putText(
                    frame,
                    f"LOITERING ({recognized_name})",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3,
                )

                # Ek aadmi ke liye ek hi baar loitering alert bhejna hai
                if track_id not in self.loitering_alerted:
                    self.loitering_alerted.add(track_id)

                    self.executor.submit(
                        self._save_and_alert_event,
                        frame.copy(),
                        track_id,
                        "Loitering",
                        recognized_name,
                        is_known,
                        duration=time_in_zone,
                    )
            else:
                # Agar loitering nhi hui but intrusion hua hai
                if self.latest_status["intrusion"]:
                    cv2.putText(
                        frame,
                        "INTRUSION DETECTED",
                        (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 165, 255),
                        3,
                    )

        self.latest_status["loitering_alert"] = loitering_active

        # Threat level decide kr rhe hain dashboard ke liye
        if loitering_active:
            self.latest_status["threat"] = "CRITICAL"
        elif self.latest_status["intrusion"]:
            self.latest_status["threat"] = "HIGH"
        else:
            self.latest_status["threat"] = "SAFE"

    def _handle_exits(self, track_ids):
        """
        Purpose:
        Jo log restricted zone se bahar chale gaye hain unka Exit Event record krna.
        """
        current_time = time.time()

        # Un logon ko dhoondo jo zone me the par ab camera me nahi hain
        # ya zone ke bahar nikal gaye hain
        zone_tracks = list(self.active_zone_tracks.keys())

        for track_id in zone_tracks:
            # Check krna function bahar defined check_intrusion karta hai
            # Yaha hum simply manenge ki agar active_tracks me hai par current frame track_ids me nhi hai, toh bahar chala gaya
            if track_id not in track_ids:
                duration = current_time - self.active_zone_tracks[track_id]

                default_face = {"name": "UNKNOWN (No Face)", "is_known": False}
                face_info = self.recognized_faces.get(track_id, default_face)

                # Background task submit kr rhe hain
                self.executor.submit(
                    self._save_and_alert_event,
                    None,
                    track_id,
                    "Zone Exit",
                    face_info["name"],
                    face_info["is_known"],
                    duration=duration,
                )

                # Unhe history se hata do
                del self.active_zone_tracks[track_id]

                if track_id in self.loitering_alerted:
                    self.loitering_alerted.remove(track_id)

    def _cleanup_old_faces(self, current_track_ids):
        """
        Purpose:
        Memory bachane ke liye un logon ka face data delete krna jo ab camera me nhi hain.
        """
        active_tids = set(current_track_ids)

        for track_id in list(self.recognized_faces.keys()):
            # Agar person camera feed me nhi hai aur zone me bhi nhi hai
            if track_id not in active_tids and track_id not in self.active_zone_tracks:
                del self.recognized_faces[track_id]

    def _save_and_alert_event(
        self,
        frame,
        track_id,
        event_type,
        recognized_name,
        is_known,
        entry_time=None,
        duration=None,
    ):
        """
        Purpose:
        Database me entry save krna aur zarurat padne pr email bhejna.
        Ye function ThreadPoolExecutor dwara background me chalaya jata hai.
        """
        image_path = ""

        # Agar frame pass kiya hai toh uska evidence image save karenge
        if frame is not None:
            image_path = save_intrusion_image(frame)

        exit_time = None
        if event_type == "Zone Exit":
            exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Database me event dal rhe hain
        save_event(
            self.user_id,
            event_type,
            image_path,
            track_id=track_id,
            entry_time=entry_time,
            exit_time=exit_time,
            duration=duration,
            recognized_name=recognized_name,
            is_known=is_known,
        )

        # Counter badhao
        self._increment_total_events()

        # Sirf unknown logo (intruders) ke liye alert bhejenge
        if not is_known and event_type in ["Intrusion", "Loitering"]:
            threat = "CRITICAL" if event_type == "Loitering" else "HIGH"
            send_intrusion_email(
                self.user_id, image_path, threat, 1, track_id, recognized_name, is_known
            )

    def _capture_loop(self, camera):
        """
        Purpose:
        Lag hatane ke liye camera se lagatar (continuously) naye frames padhna.
        """
        while self._capture_running:
            success, frame = camera.read()
            if success:
                self._latest_raw_frame = frame
            else:
                self._latest_raw_frame = None
                time.sleep(1)

    def get_jpeg(self):
        """
        Purpose:
        Flask Server is function ko call krke web browser ke liye frame mangega.
        """
        self.last_accessed = time.time()
        return self.latest_jpeg

    def get_status(self):
        """
        Purpose:
        Dashboard par statistics bhejne ke liye.
        """
        self.last_accessed = time.time()
        return self.latest_status


class CameraManager:
    """
    Ek global class jo sabhi users ke camera threads sambhalti hai (Singleton type).
    """

    _threads = {}
    _lock = Lock()

    @classmethod
    def get_thread(cls, user_id):
        """
        Purpose:
        Agar user ka thread pehle se chal rha hai toh wo return krega, nhi toh naya banayega.
        """
        with cls._lock:
            # Agar thread exist nhi krta ya band ho chuka hai
            if user_id not in cls._threads or not cls._threads[user_id].running:
                new_thread = UserCameraThread(user_id)
                new_thread.start()
                cls._threads[user_id] = new_thread

            return cls._threads[user_id]
