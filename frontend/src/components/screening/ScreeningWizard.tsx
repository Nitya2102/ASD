import { useScreening } from '@/hooks/useScreening';
import { StepIndicator } from './StepIndicator';
import { PatientInfoForm } from './PatientInfoForm';
import { QuestionnaireForm } from './QuestionnaireForm';
import { ImageCapture } from './ImageCapture';
import { ResultsDisplay } from './ResultsDisplay';

const STEPS = [
  { id: 'patient-info', label: 'Patient Info' },
  { id: 'questionnaire', label: 'Questionnaire' },
  { id: 'image-analysis', label: 'Image Analysis' },
  { id: 'results', label: 'Results' },
];

export function ScreeningWizard() {
  const {
    state,
    setPatientInfo,
    setResponse,
    setImage,
    goToStep,
    submitQuestionnaire,
    submitImage,
    skipImageAnalysis,
    reset,
  } = useScreening();

  const completedSteps = STEPS.slice(0, STEPS.findIndex(s => s.id === state.step)).map(s => s.id);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container max-w-4xl py-6">
          <h1 className="text-2xl font-semibold tracking-tight">ASD Screening Tool</h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive autism spectrum disorder screening with explainable AI
          </p>
        </div>
      </header>

      {/* Progress indicator */}
      <div className="border-b border-border bg-card/50">
        <div className="container max-w-4xl py-6">
          <StepIndicator
            steps={STEPS}
            currentStep={state.step}
            completedSteps={completedSteps}
          />
        </div>
      </div>

      {/* Main content */}
      <main className="container max-w-4xl py-8">
        <div className="clinical-card-elevated">
          {state.step === 'patient-info' && (
            <PatientInfoForm onSubmit={setPatientInfo} />
          )}

          {state.step === 'questionnaire' && (
            <QuestionnaireForm
              responses={state.responses}
              onResponse={setResponse}
              onSubmit={submitQuestionnaire}
              onBack={() => goToStep('patient-info')}
              isLoading={state.isLoading}
            />
          )}

          {state.step === 'image-analysis' && (
            <ImageCapture
              imagePreview={state.imagePreview}
              onImageSelect={setImage}
              onSubmit={submitImage}
              onSkip={skipImageAnalysis}
              onBack={() => goToStep('questionnaire')}
              isLoading={state.isLoading}
            />
          )}

          {state.step === 'results' && state.combinedResult && (
            <ResultsDisplay
              result={state.combinedResult}
              imagePreview={state.imagePreview}
              onReset={reset}
            />
          )}
        </div>

        {/* Error display */}
        {state.error && (
          <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            {state.error}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/50 mt-auto">
        <div className="container max-w-4xl py-4 text-center text-sm text-muted-foreground">
          <p>For clinical research purposes only. Not a diagnostic tool.</p>
        </div>
      </footer>
    </div>
  );
}
