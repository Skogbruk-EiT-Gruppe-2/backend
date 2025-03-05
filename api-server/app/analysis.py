from pathlib import Path
from birdnet import SpeciesPredictions, predict_species_within_audio_file
import os
import absl.logging

# Disable logging of gradient update warnings (as we only use the model for inference)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # or '2' for warning+errors only
absl.logging.set_verbosity(absl.logging.FATAL)

def raw_analyse(file_path: str):

    audio_path = Path(file_path)
    predictions = SpeciesPredictions(predict_species_within_audio_file(audio_path))

    analysis = []

    # Loop over available intervals and print predictions
    for interval, preds in predictions.items():
        print(f"Predictions for interval {interval}:")
        prediction_items = list(preds.items())
        for prediction, confidence in prediction_items:
            print(f"Predicted '{prediction}' with confidence {confidence:.2f}")
        
        analysis.append(prediction_items)
    
    return analysis

def analyse(file_path: str, confidence_threshold: float = 0.5):
    analysis = raw_analyse(file_path)
    
    classification_confidence_sums = {}
    for interval in analysis:
        for prediction, confidence in interval:
            if prediction not in classification_confidence_sums:
                classification_confidence_sums[prediction] = 0
            classification_confidence_sums[prediction] += confidence

    # Assume one bird per audio file (for simplicity)
    best_prediction = None
    best_confidence = 0
    for prediction, confidence_sum in classification_confidence_sums.items():
        if confidence_sum > best_confidence:
            best_prediction = prediction
            best_confidence = confidence_sum
    
    if best_confidence < confidence_threshold:
        return None
    else:
        return best_prediction

def process_audio_file(file_path, db, observation_id):
    try:
        # Check that the file exists
        if not os.path.exists(file_path):
            print(f"File not found at {file_path}")
            return

        classification = analyse(file_path)
        
        if classification is not None:
            # Upsert the observation with the classification
            # Classification:
            # {
            #   "value": {
            #     "classification": "bird",
            #     "is_redlisted": true
            #   },
            #   "file_path": file_path
            # }
            collection = db["observations"]
            query = {"_id": observation_id}
            update = {
                "$set": {
                    "value.classification": classification,
                    "file_path": file_path
                }
            }
            collection.update_one(query, update, upsert=True)
    except Exception as e:
        print(f"Error processing audio file at {file_path}: {e}")
        

if __name__ == "__main__":
    analysis = process_audio_file("81f3501c-14e3-43d7-a0e2-cc88d33c6615.wav", None, None)
    print(analysis)