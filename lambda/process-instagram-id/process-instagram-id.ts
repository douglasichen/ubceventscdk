interface InstagramIdEvent {
  instagramId: string;
}

async function processInstagramId(instagramId: string) {
  console.log(`Processing Instagram ID: ${instagramId}`);
}

export const handler = async (event: InstagramIdEvent): Promise<any> => {
  const { instagramId } = event;
  const alreadyProcessed = false;
  if (alreadyProcessed) {
    return {
      statusCode: 200,
      body: {
        alreadyProcessed: true,
        processed: false,
      },
    };
  }

  await processInstagramId(instagramId);

  return {
    statusCode: 200,
    body: {
      alreadyProcessed: false,
      processed: true,
    },
  };
};
