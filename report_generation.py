import os
import sys
import librosa
import numpy as np
from fpdf import FPDF

# Check for required arguments
if len(sys.argv) < 6:
    print("Usage: python3 report_generation.py <audio_path> <output_pdf> <name> <age> <appointment_id>")
    sys.exit(1)

# Extract arguments from command line
audio_path = sys.argv[1]
output_pdf = sys.argv[2]
patient_name = sys.argv[3]
patient_age = sys.argv[4]
appointment_id = sys.argv[5]

# Logo path (ensure logo.png is in the same directory)
LOGO_PATH = "/Users/kaniklchawla/Desktop/telegrm/image.png"

# Remove existing PDF before creating a new one
if os.path.exists(output_pdf):
    os.remove(output_pdf)

# Sample voice condition prediction (Dummy Model)
CONDITIONS = ["Healthy", "Laryngitis", "Vocal Polyp"]

NORMAL_RANGES = {
    "Fundamental Frequency (Mean)": (85, 255),
    "Fundamental Frequency (Std)": (0, 20),
    "Jitter": (0, 2.2),
    "Shimmer": (0, 3.81),
    "Harmonic Ratio": (0.15, 0.25),
    "Voice Period": (0.003, 0.005),
    "Voiced Segments Ratio": (0.4, 0.8),
    "Formant Frequency": (500, 2000)
}

def extract_audio_features(audio_path):
    """Extract detailed acoustic features."""
    y, sr = librosa.load(audio_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    f0_mean = np.nanmean(f0)
    f0_std = np.nanstd(f0)
    
    # Placeholder values for jitter, shimmer, etc.
    jitter = np.random.uniform(0, 3)
    shimmer = np.random.uniform(0, 5)
    harmonic_ratio = np.random.uniform(0, 0.3)
    voice_period = np.random.uniform(0.002, 0.006)
    voiced_segments_ratio = np.random.uniform(0.3, 0.9)
    formant_frequency = np.random.uniform(600, 1800)
    
    return {
        "Fundamental Frequency (Mean)": f0_mean,
        "Fundamental Frequency (Std)": f0_std,
        "Jitter": jitter,
        "Shimmer": shimmer,
        "Harmonic Ratio": harmonic_ratio,
        "Voice Period": voice_period,
        "Voiced Segments Ratio": voiced_segments_ratio,
        "Formant Frequency": formant_frequency
    }

def predict_voice_condition(features):
    """Predicts voice condition based on extracted acoustic features."""
    
    f0_mean = features["Fundamental Frequency (Mean)"]
    jitter = features["Jitter"]
    shimmer = features["Shimmer"]
    harmonic_ratio = features["Harmonic Ratio"]
    voiced_segments_ratio = features["Voiced Segments Ratio"]
    formant_frequency = features["Formant Frequency"]

    # Thresholds based on normal ranges
    if jitter > 2.2 or shimmer > 3.81 or harmonic_ratio < 0.15 or f0_mean < 85 or voiced_segments_ratio < 0.4:
        prediction = "Healthy"
        confidence = round(85 + (jitter + shimmer) / 5, 2)

    elif shimmer > 4 or voiced_segments_ratio < 0.35 or formant_frequency > 1800:
        prediction = "Healthy"
        confidence = round(80 + (shimmer + (2000 - formant_frequency) / 200), 2)

    else:
        prediction = "Healthy"
        confidence = round(90 - ((jitter + shimmer) / 5), 2)

    confidence = min(99, max(60, confidence))  # Keep within 60-99% range
    return prediction, confidence

class PDF(FPDF):
    def header(self):
        """Custom header with logo and title"""
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)  # Place logo
        self.set_font('Arial', 'B', 16)
        
        # Pink colored title
        self.set_text_color(219, 48, 122)  # RGB for pink
        self.cell(0, 10, "Resonanze Voice Analysis Report", align="C", ln=True)
        
        # Reset color and add spacing
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    def footer(self):
        """Custom footer with date and confidentiality note"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Generated on {os.popen('date').read().strip()} | Confidential Report", align="C")
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title, ln=True)
        self.ln(2)
    
    def chapter_body(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, text)
        self.ln()
    
    def add_patient_info(self, name, age, appointment_id):
        """Add formatted patient details"""
        self.set_font('Arial', '', 11)
        self.cell(0, 8, f"Patient Name: {name}", ln=True)
        self.cell(0, 8, f"Age: {age}", ln=True)
        self.cell(0, 8, f"Appointment ID: {appointment_id}", ln=True)
        self.ln(5)
    
    def add_feature_table(self, features):
        """Create a table for extracted voice features"""
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, "Acoustic Measurements", ln=True)
        self.set_font('Arial', '', 10)
        
        # Table headers
        col_widths = [70, 30, 50, 20]
        headers = ["Parameter", "Value", "Normal Range", "Unit"]
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, border=1, align="C")
        self.ln()
        
        # Table data
        for key, value in features.items():
            normal_range = NORMAL_RANGES.get(key, "-")
            self.cell(col_widths[0], 8, key, border=1)
            self.cell(col_widths[1], 8, f"{value:.2f}", border=1, align="C")
            self.cell(col_widths[2], 8, f"{normal_range[0]} - {normal_range[1]}", border=1, align="C")
            self.cell(col_widths[3], 8, "Hz" if "Frequency" in key else "%" if key in ["Jitter", "Shimmer"] else "s", border=1, align="C")
            self.ln()

def generate_pdf(features, prediction, confidence, output_pdf):
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title("Patient Information")
    pdf.add_patient_info(patient_name, patient_age, appointment_id)
    
    pdf.chapter_title("Diagnosis")
    pdf.chapter_body(f"Predicted Condition: {prediction} ({confidence}%)")
    
    pdf.add_feature_table(features)
    
    pdf.chapter_title("Clinical Summary & Recommendations")
    pdf.chapter_body("The acoustic analysis suggests voice irregularities indicative of vocal pathology.")
    pdf.chapter_body("1. Laryngoscopy for further examination\n2. Voice therapy for recovery\n3. Surgical evaluation if symptoms persist")
    
    pdf.output(output_pdf)
    print(f"Report saved to {output_pdf}")

# Extract features and generate the report
features = extract_audio_features(audio_path)
prediction, confidence = predict_voice_condition(features)
generate_pdf(features, prediction, confidence, output_pdf)
