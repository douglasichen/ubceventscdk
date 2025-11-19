interface InstagramIdEvent {
  instagramId: string;
}

export const handler = async (event: InstagramIdEvent): Promise<any> => {
  console.log(JSON.stringify(event));
  return {
    statusCode: 200,
    body: JSON.stringify({ message: "Instagram ID processed successfully" }),
  }
};
