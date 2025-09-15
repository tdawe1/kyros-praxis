import { redirect } from 'next/navigation'

export default function LoginAliasPage() {
  // Redirect legacy/login path to the actual auth page
  redirect('/auth')
}

