/* original code from Joan
 * modified by Cerem Cem ASLAN
 * 28.12.2014
 * License: Do whatever you want to do
 */

#define GPIO 4

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h> 

#include <pigpio.h>

/*
gcc -o swave swave.c -lpigpio -lrt -lpthread
sudo ./swave
*/

/* generates a simple stepper ramp. */
int ramp(
   unsigned start_delay,
   unsigned final_delay,
   //unsigned step,
   unsigned count, 
   unsigned rise_time
        )
{
   unsigned step; 
   int i, j, p, npulses, np, wid=-1, each_step_width, step_pulse_count;
   rawWaveInfo_t waveInfo;
   rawCbs_t *cbp1, *cbp2;
   gpioPulse_t *pulses;

   step = (start_delay - final_delay) / count; 

   each_step_width = (rise_time * 1000) / count ; 
   printf("each step width: %d\n microseconds", each_step_width); 

   //npulses = (((start_delay-final_delay) / step) + 1 ) * count * 2;

   npulses = 10; 
    for (i=start_delay; i>=final_delay; i-=step)
    {
        step_pulse_count = each_step_width / i; 
        for (j=0; j<step_pulse_count; j++)
        {
          npulses += 2; 
        }
    }
    
    printf("number of pulses: %d", npulses); 


    //npulses += 10;
   

   pulses = (gpioPulse_t*) malloc(npulses * sizeof(gpioPulse_t));

   
   if (pulses)
   {
      p = 0;
      
      
      for (i=start_delay; i>=final_delay; i-=step)
      {
         step_pulse_count = each_step_width / i; 
         for (j=0; j<step_pulse_count; j++)
         {
            pulses[p].gpioOn = (1<<GPIO);
            pulses[p].gpioOff = 0;
            pulses[p].usDelay = i/2;
            p++;

            pulses[p].gpioOn = 0;
            pulses[p].gpioOff = (1<<GPIO);
            pulses[p].usDelay = i/2;
            p++;
         }
      }

       /* dummy last pulse, will never be executed */

      pulses[p].gpioOn = (1<<GPIO);
      pulses[p].gpioOff = 0;
      pulses[p].usDelay = i;
      p++;

      np = gpioWaveAddGeneric(p, pulses);

      wid = gpioWaveCreate();

      if (wid >= 0)
      {
         waveInfo = rawWaveInfo(wid);
         /*
         -7 gpio off         next-> -6
         -6 delay final step next-> -5
         -5 gpio on          next-> -4
         -4 delay final step next-> -3
         -3 gpio off         next-> -2
         -2 delay final step next-> -1
         -1 dummy gpio on    next->  0
          0 dummy delay      next-> first CB
         */
         /* patch -2 to point back to -5 */
         cbp1 = rawWaveCBAdr(waveInfo.topCB-2);
         cbp2 = rawWaveCBAdr(waveInfo.topCB-6);
         cbp1->next = cbp2->next;
      }
      free(pulses);
   }
   return wid;
}

#define START_DELAY 100 //microseconds
#define FINAL_DELAY 25   // microseconds
#define STEP_COUNT 50
#define RISE_TIME 100 // milliseconds

void start_sig_handler(int signo)
{
  while (signo == SIGCONT)
  {
    printf("received start signal\n");
    int arg, pos = 0, np, wid, steps;

    gpioWaveTxStop();
    gpioWaveClear(); 

    wid = ramp(START_DELAY, FINAL_DELAY, STEP_COUNT, RISE_TIME);

    if (wid >= 0)
    {
        gpioWaveTxSend(wid, PI_WAVE_MODE_ONE_SHOT);
    }
    break; 
  }
}


void stop_sig_handler(int signo)
{
  if (signo == SIGUSR2)
  {  
    printf("received stop signal\n");
    gpioWaveTxStop();
    gpioWaveClear(); 
  }
   
}


uint32_t HB_TICK; 

void heartbeat_sig_handler(int signo)
{
  if (signo == SIGUSR1)
  {  
    //printf("received heartbeat\n");
    HB_TICK = gpioTick(); 
  }
}

int pigpio_watchdog()
{
  static uint32_t timeout = 500000; // microseconds
  if (gpioTick() > HB_TICK + timeout)
  {
    printf("watchdog timed out. HB_TICK: %d, gpioTick: %d ||| ", HB_TICK, gpioTick()); 
    time_sleep(0.1);
    return 1;
  }
  return 0; 
}

  
int main(int argc, char *argv[])
{
  
  printf("starting swave..."); 
  if (gpioInitialise() < 0) 
  {
    printf("can not initialize gpio library"); 
    return 1;
  }
  else
  {
    printf("started swave");
    
  }
  
  gpioSetSignalFunc(SIGCONT, start_sig_handler); 
  gpioSetSignalFunc(SIGUSR1, heartbeat_sig_handler); 
  gpioSetSignalFunc(SIGUSR2, stop_sig_handler); 
  
  // prevent shutdowns by unimportant signals
  gpioSetSignalFunc(28, heartbeat_sig_handler); 
  
  gpioSetMode(GPIO, PI_OUTPUT);

  printf("getting into loop...");
  HB_TICK = gpioTick();
  while(1)
  {
    //printf("looping...");
    if (pigpio_watchdog() > 0)
    {
      // stop the output in order not to 
      // physically damage anything without intention
      gpioWaveTxStop();
      gpioWaveClear(); 
      //gpioTerminate();
      //break; 
    }
    time_sleep(.1);
  }

}
