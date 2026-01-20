import { useState } from 'react';
import { PatientInfo } from '@/types/asd';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface PatientInfoFormProps {
  onSubmit: (info: PatientInfo) => void;
}

export function PatientInfoForm({ onSubmit }: PatientInfoFormProps) {
  const [age, setAge] = useState<string>('');
  const [sex, setSex] = useState<'male' | 'female' | null>(null);
  const [jaundice, setJaundice] = useState<'yes' | 'no' | null>(null);
  const [familyAsd, setFamilyAsd] = useState<'yes' | 'no' | null>(null);

  const isValid = age && parseInt(age) > 0 && sex && jaundice !== null && familyAsd !== null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;

    onSubmit({
      age: parseInt(age),
      sex: sex!,
      jaundice: jaundice!,
      familyAsd: familyAsd!,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-slide-up">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Patient Information</h2>
        <p className="text-muted-foreground text-sm">
          Please provide basic information about the child being screened.
        </p>
      </div>

      <div className="grid gap-6">
        <div className="space-y-2">
          <Label htmlFor="age">Age (in months)</Label>
          <Input
            id="age"
            type="number"
            min="1"
            max="216"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="e.g., 24"
            className="max-w-[200px]"
          />
        </div>

        <div className="space-y-3">
          <Label>Sex</Label>
          <div className="flex gap-3">
            {(['male', 'female'] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setSex(option)}
                className={cn(
                  'questionnaire-option capitalize',
                  sex === option && 'questionnaire-option-selected'
                )}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Label>Born with jaundice?</Label>
          <div className="flex gap-3">
            {(['yes', 'no'] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setJaundice(option)}
                className={cn(
                  'questionnaire-option capitalize',
                  jaundice === option && 'questionnaire-option-selected'
                )}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Label>Family member with ASD?</Label>
          <div className="flex gap-3">
            {(['yes', 'no'] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setFamilyAsd(option)}
                className={cn(
                  'questionnaire-option capitalize',
                  familyAsd === option && 'questionnaire-option-selected'
                )}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Button type="submit" disabled={!isValid} size="lg">
        Continue to Questionnaire
      </Button>
    </form>
  );
}
