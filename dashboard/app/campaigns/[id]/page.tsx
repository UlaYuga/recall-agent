import { CampaignWorkspace } from '../../../components/CampaignWorkspace';

interface Props {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({ params }: Props) {
  const { id } = await params;
  return <CampaignWorkspace campaignId={id} />;
}
