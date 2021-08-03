close all;
clc
clear;
%
% plot travel time versus hypocenter distance.
% Input file: t_dist.dat
%
% M. Zhang modified from Hao Guo

distmax = 150
tmax = 30

%% separate P and S t-dist data.
t_d = load('t_dist.dat');
n1 = 0; n2 = 0;
for i = 1:length(t_d(:,1))
    if t_d(i,3)==1
        n1 = n1+1;
        t_d_P(n1,1) = t_d(i,1);
        t_d_P(n1,2) = t_d(i,2);
    elseif t_d(i,3)==2
        n2 = n2+1;
        t_d_S(n2,1) = t_d(i,1);
        t_d_S(n2,2) = t_d(i,2);
    end
end
%% plot t-dist curve of P wave
figure;
subplot(1,2,1);
plot(t_d_P(:,2),t_d_P(:,1),'r.');hold on;

axis([0 distmax 0 tmax]);
title('t-dist curve of P');
xlabel('Hypocenter Distance (km)');ylabel('Travel Time (s)');

%% plot t-dist curve of S wave
subplot(1,2,2); 
plot(t_d_S(:,2),t_d_S(:,1),'r.');hold on;

axis([0 distmax 0 tmax]);
title('t-dist curve of S');
xlabel('Hypocenter Distance (km)');
%print('-depsc2','t_dist','-r300');
saveas(gcf,'t_dist.pdf');
