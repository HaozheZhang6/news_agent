-- Minimal seed: insert only a demo user row into existing public.users
-- No new tables or columns are referenced.

INSERT INTO public.users (id, email, subscription_tier)
VALUES (
    '03f6b167-0c4d-4983-a380-54b8eb42f830'::uuid,
    'demo@voicenews.test',
    'free'
)
ON CONFLICT (id) DO UPDATE SET
  email = EXCLUDED.email,
  subscription_tier = EXCLUDED.subscription_tier,
  updated_at = NOW();

-- Verify
SELECT 'Demo User:' as info;
SELECT id, email, subscription_tier FROM public.users WHERE id = '03f6b167-0c4d-4983-a380-54b8eb42f830'::uuid;
