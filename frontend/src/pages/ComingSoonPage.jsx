import { Hammer } from 'lucide-react'

import PageHeader from '../components/layout/PageHeader'
import { EmptyState } from '../components/ui'

/** Page provisoire des sections encore en cours de développement. */
export default function ComingSoonPage({ title }) {
  return (
    <>
      <PageHeader title={title} />
      <EmptyState icon={Hammer} title="Bientôt disponible" />
    </>
  )
}
