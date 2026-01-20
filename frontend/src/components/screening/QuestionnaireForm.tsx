import { QuestionnaireResponses, QUESTIONNAIRE_QUESTIONS } from '@/types/asd';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface QuestionnaireFormProps {
  responses: QuestionnaireResponses;
  onResponse: (questionId: keyof QuestionnaireResponses, value: 'yes' | 'no') => void;
  onSubmit: () => void;
  onBack: () => void;
  isLoading: boolean;
}

export function QuestionnaireForm({
  responses,
  onResponse,
  onSubmit,
  onBack,
  isLoading,
}: QuestionnaireFormProps) {
  const answeredCount = Object.values(responses).filter(v => v !== null).length;
  const isComplete = answeredCount === 10;
  const progress = (answeredCount / 10) * 100;

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Behavioral Questionnaire</h2>
        <p className="text-muted-foreground text-sm">
          Answer all 10 questions based on your child's typical behavior.
        </p>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>{answeredCount} of 10 questions answered</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-6">
        {QUESTIONNAIRE_QUESTIONS.map((question, index) => {
          const id = question.id as keyof QuestionnaireResponses;
          const response = responses[id];

          return (
            <div
              key={question.id}
              className={cn(
                'p-4 rounded-lg border transition-colors',
                response !== null ? 'border-primary/30 bg-primary/5' : 'border-border'
              )}
            >
              <div className="flex items-start gap-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-sm font-medium text-secondary-foreground">
                  {index + 1}
                </span>
                <div className="flex-1 space-y-3">
                  <p className="font-medium leading-relaxed">{question.text}</p>
                  <div className="flex gap-3">
                    {(['yes', 'no'] as const).map((option) => (
                      <button
                        key={option}
                        type="button"
                        onClick={() => onResponse(id, option)}
                        className={cn(
                          'questionnaire-option w-20 capitalize',
                          response === option && 'questionnaire-option-selected'
                        )}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onSubmit} disabled={!isComplete || isLoading} size="lg">
          {isLoading ? 'Analyzing...' : 'Analyze Responses'}
        </Button>
      </div>
    </div>
  );
}
