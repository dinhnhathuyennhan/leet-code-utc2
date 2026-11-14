import type { SessionDetailData } from "@/lib/types/course";
import type { SessionStatus } from "@/lib/helpers/session-status";

type Props = {
  alert: SessionDetailData["alert"];
  status: SessionStatus;
  listHref: string;
};

export function SessionDeadlineAlert(props: Props) {
  void props;
  return null;
}