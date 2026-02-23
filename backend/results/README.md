# Backend Results Directory Structure

## Training Data Storage
- `training_data/` - JSON files for model retraining
  - `segmentation_results.json` - Processed text results for training
  - `user_feedback.json` - User corrections and feedback
  - `error_patterns.json` - Common segmentation errors

## User Exports
- `user_exports/` - Temporary storage for user-requested exports
  - Timestamped folders for batch exports
  - Auto-cleanup after 7 days

## Data Formats
- Training data uses JSON schema compatible with existing CRF trainers
- Includes metadata: timestamp, user_id (if available), confidence scores
- Supports incremental learning without full retraining